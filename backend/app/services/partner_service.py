"""Delivery-partner directory (additive feature — section 1/7).

Reuses existing data rather than duplicating it: a partner's vehicles are
found by matching the existing `Vehicle.partner` string (unchanged column)
against `DeliveryPartner.name`; "current delivery"/"completed"/"active"
counts are derived from the existing `deliveries` table, not recomputed or
stored separately.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Delivery, DeliveryPartner, Vehicle


@dataclass
class PartnerVehicleSummary:
    vehicle_id: str
    type: str
    capacity_kg: float
    status: str
    current_delivery_id: str | None


@dataclass
class PartnerSummary:
    id: str
    name: str
    contact_person: str
    phone: str
    vehicles: list[PartnerVehicleSummary]
    completed_deliveries: int
    active_deliveries: int


def _summarize(db: Session, partner: DeliveryPartner, vehicles: list[Vehicle]) -> PartnerSummary:
    vehicle_ids = {v.id for v in vehicles}
    deliveries: list[Delivery] = (
        db.query(Delivery).filter(Delivery.vehicle_id.in_(vehicle_ids)).all() if vehicle_ids else []
    )
    completed = sum(1 for d in deliveries if d.status == "Delivered")
    active = sum(1 for d in deliveries if d.status != "Delivered")

    return PartnerSummary(
        id=partner.id,
        name=partner.name,
        contact_person=partner.contact_person,
        phone=partner.phone,
        vehicles=[
            PartnerVehicleSummary(
                vehicle_id=v.id,
                type=v.type,
                capacity_kg=v.capacity_kg,
                status=v.status,
                current_delivery_id=v.current_delivery_id,
            )
            for v in vehicles
        ],
        completed_deliveries=completed,
        active_deliveries=active,
    )


def list_partners(db: Session) -> list[PartnerSummary]:
    partners = db.query(DeliveryPartner).order_by(DeliveryPartner.id).all()
    all_vehicles = db.query(Vehicle).all()
    vehicles_by_partner_name: dict[str, list[Vehicle]] = {}
    for v in all_vehicles:
        vehicles_by_partner_name.setdefault(v.partner, []).append(v)

    return [_summarize(db, p, vehicles_by_partner_name.get(p.name, [])) for p in partners]


def get_partner(db: Session, partner_id: str) -> PartnerSummary | None:
    partner = db.get(DeliveryPartner, partner_id)
    if partner is None:
        return None
    vehicles = db.query(Vehicle).filter(Vehicle.partner == partner.name).all()
    return _summarize(db, partner, vehicles)
