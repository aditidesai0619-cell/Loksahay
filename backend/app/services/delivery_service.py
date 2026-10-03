from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Delivery, SourceInventory, Vehicle
from app.services.tracking_location import location_for_stage
from app.utils.ids import next_id
from app.utils.time import now as time_now

LIFECYCLE = ["Assigned", "Accepted", "Picked Up", "In Transit", "Arrived", "Delivered"]

VEHICLE_STATUS_FOR_STAGE = {
    "Assigned": "Assigned",
    "Accepted": "Assigned",
    "Picked Up": "In Transit",
    "In Transit": "In Transit",
    "Arrived": "In Transit",
    "Delivered": "Delivered",
}


def list_deliveries(db: Session) -> list[Delivery]:
    return db.query(Delivery).order_by(Delivery.id).all()


def get_delivery(db: Session, delivery_id: str) -> Delivery | None:
    return db.get(Delivery, delivery_id)


def advance_status(db: Session, delivery_id: str, new_status: str, note: str | None = None) -> Delivery:
    delivery = get_delivery(db, delivery_id)
    if delivery is None:
        raise LookupError(f"Delivery {delivery_id} not found")
    if new_status not in LIFECYCLE:
        raise ValueError(f"Invalid delivery status '{new_status}'")

    current_idx = LIFECYCLE.index(delivery.status)
    new_idx = LIFECYCLE.index(new_status)
    if new_idx < current_idx:
        raise ValueError(f"Cannot move delivery backward from '{delivery.status}' to '{new_status}'")
    if new_idx > current_idx + 1:
        raise ValueError(
            f"Cannot skip stages: delivery is at '{delivery.status}', next valid stage is "
            f"'{LIFECYCLE[current_idx + 1]}'"
        )

    delivery.status = new_status
    from app.models import TrackingEvent

    location = location_for_stage(db, delivery.route_node_ids, new_status)
    db.add(
        TrackingEvent(
            id=next_id(db, TrackingEvent, "TRK", pad=3),
            delivery_id=delivery.id,
            status=new_status,
            timestamp=time_now(),
            note=note,
            lat=location[0] if location else None,
            lng=location[1] if location else None,
        )
    )

    vehicle = db.get(Vehicle, delivery.vehicle_id)
    if vehicle is not None:
        vehicle.status = VEHICLE_STATUS_FOR_STAGE[new_status]

    if new_status == "Delivered":
        for item in delivery.cargo:
            line = (
                db.query(SourceInventory)
                .filter(SourceInventory.source_id == delivery.source_id, SourceInventory.resource == item["resource"])
                .one_or_none()
            )
            if line is not None:
                line.delivered = min(line.allocated, line.delivered + item["quantity"])

    db.commit()
    db.refresh(delivery)
    return delivery
