"""Orchestrates the allocation engine against the live database:
persisting proposals, and handling coordinator accept/modify/reject
decisions (which reserve/release real inventory and vehicle capacity).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.algorithms.allocation_engine import run_allocation
from app.algorithms.dto import cargo_weight_kg
from app.models import (
    AffectedRequest,
    Allocation,
    Delivery,
    SourceInventory,
    SupplySource,
    TrackingEvent,
    Vehicle,
    VehicleCargo,
)
from app.services import converters
from app.services.config_service import get_or_create_config, weights_from_config
from app.services.plan_snapshot_service import record_snapshot
from app.services.tracking_location import location_for_stage
from app.utils.ids import next_id
from app.utils.time import now as time_now


def _request_status(required: float, allocated: float) -> str:
    if allocated >= required - 1e-6:
        return "Fulfilled"
    if allocated > 0:
        return "Partial"
    return "Unfulfilled"


def run_allocation_and_persist(db: Session, *, snapshot_label: str = "allocation.run") -> list[Allocation]:
    """Re-plan open demand. Existing Accepted/Modified allocations (and
    their deliveries) are left untouched — they are committed. Any
    previously 'Proposed' allocation is cleared (its reservation released)
    and the engine is re-run for whatever demand/capacity remains open.
    """
    config = get_or_create_config(db)
    weights = weights_from_config(config)

    # Release previously-Proposed reservations before re-running.
    for alloc in db.query(Allocation).filter(Allocation.status == "Proposed").all():
        _release_reservation(db, alloc)
        db.delete(alloc)
    db.commit()

    graph = converters.build_graph(db)
    requests = converters.load_requests(db)  # allocated already reflects committed (Accepted/Modified) sums
    sources = converters.load_sources(db)  # inventory.allocated already reflects committed sums
    vehicles = converters.load_vehicles(db)  # status already reflects committed assignments

    now = time_now()
    results, unmet, priorities = run_allocation(
        requests, sources, vehicles, graph, weights, config.minimum_coverage_pct, now
    )

    created: list[Allocation] = []
    for res in results:
        alloc_id = next_id(db, Allocation, "ALC")
        breakdown = priorities.get(res.request_id)
        alloc = Allocation(
            id=alloc_id,
            request_id=res.request_id,
            source_id=res.source_id,
            vehicle_id=res.vehicle_id,
            route_node_ids=res.route_node_ids,
            route_edge_ids=res.route_edge_ids,
            distance_km=res.distance_km,
            resource=res.resource,
            quantity=res.quantity,
            unit=res.unit,
            eta=res.eta,
            deadline=res.deadline,
            meets_deadline=res.meets_deadline,
            priority_score=res.priority_score,
            priority_breakdown=(
                {
                    "urgencyScore": breakdown.urgency_score,
                    "populationNeedScore": breakdown.population_need_score,
                    "supplyDeficitScore": breakdown.supply_deficit_score,
                    "accessibilityScore": breakdown.accessibility_score,
                }
                if breakdown is not None
                else None
            ),
            status="Proposed",
            reasons=res.reasons,
            created_at=now,
        )
        db.add(alloc)
        db.flush()  # make this id visible to the next next_id() lookup
        created.append(alloc)

        # Reserve inventory + mark vehicle busy for this proposal.
        line = (
            db.query(SourceInventory)
            .filter(SourceInventory.source_id == res.source_id, SourceInventory.resource == res.resource)
            .one()
        )
        line.allocated += res.quantity
        vehicle = db.get(Vehicle, res.vehicle_id)
        if vehicle is not None and vehicle.status == "Available":
            vehicle.status = "Assigned"

    # Sync request.allocated / status / reason from the engine's view.
    req_rows = {r.id: r for r in db.query(AffectedRequest).all()}
    allocated_by_request: dict[str, float] = {r.id: r.allocated for r in requests}
    for req_id, allocated in allocated_by_request.items():
        row = req_rows[req_id]
        row.allocated = allocated
        row.status = _request_status(row.required, allocated)
    for u in unmet:
        row = req_rows[u.request_id]
        row.reason = u.reason
        row.alternative_source_name = u.alternative_source_name
        row.alternative_eta = u.alternative_eta
    for req_id, row in req_rows.items():
        if req_id not in {u.request_id for u in unmet}:
            row.reason = None
            row.alternative_source_name = None
            row.alternative_eta = None

    config.plan_generated_at = now
    db.commit()

    record_snapshot(db, label=snapshot_label)
    return created


def _release_reservation(db: Session, alloc: Allocation) -> None:
    line = (
        db.query(SourceInventory)
        .filter(SourceInventory.source_id == alloc.source_id, SourceInventory.resource == alloc.resource)
        .one_or_none()
    )
    if line is not None:
        line.allocated = max(0.0, line.allocated - alloc.quantity)

    vehicle = db.get(Vehicle, alloc.vehicle_id)
    if vehicle is not None and vehicle.current_delivery_id is None and vehicle.status != "Unavailable":
        vehicle.status = "Available"

    req = db.get(AffectedRequest, alloc.request_id)
    if req is not None:
        req.allocated = max(0.0, req.allocated - alloc.quantity)
        req.status = _request_status(req.required, req.allocated)


def accept_allocation(db: Session, allocation_id: str) -> Allocation:
    alloc = _get_allocation_or_404(db, allocation_id)
    if alloc.status == "Rejected":
        raise ValueError("Cannot accept a rejected allocation")
    alloc.status = "Accepted"
    _ensure_delivery(db, alloc)
    db.commit()
    db.refresh(alloc)
    return alloc


def modify_allocation(db: Session, allocation_id: str, quantity: float) -> Allocation:
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    alloc = _get_allocation_or_404(db, allocation_id)
    if alloc.status == "Rejected":
        raise ValueError("Cannot modify a rejected allocation")

    line = (
        db.query(SourceInventory)
        .filter(SourceInventory.source_id == alloc.source_id, SourceInventory.resource == alloc.resource)
        .one()
    )
    vehicle = db.get(Vehicle, alloc.vehicle_id)
    if vehicle is None:
        raise ValueError("Vehicle no longer exists")

    delta = quantity - alloc.quantity
    remaining_capacity = line.available - line.allocated  # before releasing current reservation
    if delta > 0 and delta > remaining_capacity:
        raise ValueError(
            f"Requested quantity {quantity:g} exceeds remaining inventory "
            f"({remaining_capacity + alloc.quantity:g} {alloc.unit} available at this source)"
        )
    unit_cap = vehicle.capacity_kg / max(cargo_weight_kg(alloc.resource, 1.0), 0.001)
    if quantity > unit_cap:
        raise ValueError(f"Requested quantity {quantity:g} exceeds vehicle {vehicle.id} capacity ({unit_cap:g} {alloc.unit})")

    line.allocated += delta
    req = db.get(AffectedRequest, alloc.request_id)
    if req is not None:
        req.allocated = max(0.0, req.allocated + delta)
        req.status = _request_status(req.required, req.allocated)

    alloc.quantity = quantity
    alloc.status = "Modified"
    alloc.reasons = [*alloc.reasons, f"Quantity modified by coordinator to {quantity:g} {alloc.unit}"]
    _ensure_delivery(db, alloc, cargo_quantity=quantity)
    db.commit()
    db.refresh(alloc)
    return alloc


def reject_allocation(db: Session, allocation_id: str) -> Allocation:
    alloc = _get_allocation_or_404(db, allocation_id)
    if alloc.status == "Rejected":
        return alloc
    _release_reservation(db, alloc)
    alloc.status = "Rejected"

    delivery = db.query(Delivery).filter(Delivery.allocation_id == alloc.id).one_or_none()
    if delivery is not None:
        db.delete(delivery)
    vehicle = db.get(Vehicle, alloc.vehicle_id)
    if vehicle is not None:
        vehicle.current_delivery_id = None
        for cargo in list(vehicle.cargo):
            db.delete(cargo)

    db.commit()
    db.refresh(alloc)
    return alloc


def _ensure_delivery(db: Session, alloc: Allocation, *, cargo_quantity: float | None = None) -> Delivery:
    delivery = db.query(Delivery).filter(Delivery.allocation_id == alloc.id).one_or_none()
    qty = cargo_quantity if cargo_quantity is not None else alloc.quantity
    source = db.get(SupplySource, alloc.source_id)
    request = db.get(AffectedRequest, alloc.request_id)
    vehicle = db.get(Vehicle, alloc.vehicle_id)
    assert source is not None and request is not None and vehicle is not None

    if delivery is None:
        delivery_id = next_id(db, Delivery, "D")
        delivery = Delivery(
            id=delivery_id,
            allocation_id=alloc.id,
            vehicle_id=alloc.vehicle_id,
            request_id=alloc.request_id,
            source_id=alloc.source_id,
            route_node_ids=alloc.route_node_ids,
            route_edge_ids=alloc.route_edge_ids,
            distance_km=alloc.distance_km,
            cargo=[{"resource": alloc.resource, "quantity": qty, "unit": alloc.unit}],
            origin_name=source.name,
            destination_name=request.area_name,
            eta=alloc.eta,
            deadline=alloc.deadline,
            status="Assigned",
            created_at=time_now(),
        )
        db.add(delivery)
        db.flush()
        origin = location_for_stage(db, delivery.route_node_ids, "Assigned")
        db.add(
            TrackingEvent(
                id=next_id(db, TrackingEvent, "TRK", pad=3),
                delivery_id=delivery.id,
                status="Assigned",
                timestamp=time_now(),
                note="Allocation confirmed by coordinator",
                lat=origin[0] if origin else None,
                lng=origin[1] if origin else None,
            )
        )
    else:
        delivery.cargo = [{"resource": alloc.resource, "quantity": qty, "unit": alloc.unit}]
        delivery.eta = alloc.eta

    vehicle.status = "Assigned" if vehicle.status != "Unavailable" else vehicle.status
    vehicle.current_delivery_id = delivery.id
    for cargo in list(vehicle.cargo):
        db.delete(cargo)
    db.add(VehicleCargo(vehicle_id=vehicle.id, resource=alloc.resource, quantity=qty, unit=alloc.unit))

    return delivery


def _get_allocation_or_404(db: Session, allocation_id: str) -> Allocation:
    alloc = db.get(Allocation, allocation_id)
    if alloc is None:
        raise LookupError(f"Allocation {allocation_id} not found")
    return alloc
