"""Dynamic replanning (section 21).

`trigger_replan` represents a REAL network change (unlike scenario
simulation, which is hypothetical): the road/vehicle/inventory mutation
is persisted immediately. It then finds the committed, in-flight
allocation(s) that change invalidates, recomputes the best alternative
for the most-affected one using the same engine logic, and records a
`ReplanEvent` (old plan vs. new plan) for the coordinator to review.
`apply_replan` commits that specific reroute; `dismiss_replan` discards
the suggestion (the underlying disruption remains, but the original plan
is left as-is for the coordinator to handle manually).
"""

from __future__ import annotations

from dataclasses import replace

from sqlalchemy.orm import Session

from app.algorithms.allocation_engine import run_allocation
from app.algorithms.dto import RequestDTO
from app.algorithms.graph import RoadGraph
from app.algorithms.scenario_mutations import ScenarioActionInput
from app.models import Allocation, Delivery, ReplanEvent, RoadEdge, SourceInventory, Vehicle
from app.services import converters
from app.services.config_service import get_or_create_config, weights_from_config
from app.services.plan_snapshot_service import compute_live_metrics, record_snapshot
from app.services.scenario_service import simulate_scenario
from app.utils.ids import next_id
from app.utils.time import now as time_now

def _metrics_to_camel(m: dict) -> dict:
    """compute_live_metrics() returns snake_case keys; ReplanEvent.metrics_before
    /metrics_after must both be camelCase (matching ScenarioMetrics on the
    frontend) — this is the one place that conversion happens, so the two
    can never drift into mismatched key casing."""
    return {
        "demandFulfilledPct": m["demand_fulfilled_pct"],
        "criticalDemandFulfilledPct": m["critical_demand_fulfilled_pct"],
        "onTimeDeliveryPct": m["on_time_delivery_pct"],
        "totalDistanceKm": m["total_distance_km"],
        "vehicleTrips": m["vehicle_trips"],
        "unmetDemandUnits": m["unmet_demand_units"],
    }


TRIGGER_TO_SCENARIO_TYPE = {
    "Road Blocked": "Block Road",
    "Vehicle Unavailable": "Remove Vehicle",
    "Inventory Shortfall": "Reduce Inventory",
}


def list_replans(db: Session) -> list[ReplanEvent]:
    return db.query(ReplanEvent).order_by(ReplanEvent.triggered_at.desc()).all()


def get_replan(db: Session, replan_id: str) -> ReplanEvent | None:
    return db.get(ReplanEvent, replan_id)


def _find_affected_committed_allocation(db: Session, trigger_type: str, target_id: str) -> Allocation | None:
    committed = (
        db.query(Allocation)
        .filter(Allocation.status.in_(("Accepted", "Modified")))
        .join(Delivery, Delivery.allocation_id == Allocation.id)
        .filter(Delivery.status != "Delivered")
        .all()
    )
    if trigger_type == "Road Blocked":
        candidates = [a for a in committed if target_id in a.route_edge_ids]
    elif trigger_type == "Vehicle Unavailable":
        candidates = [a for a in committed if a.vehicle_id == target_id]
    elif trigger_type == "Inventory Shortfall":
        candidates = []
        for a in committed:
            if a.source_id != target_id:
                continue
            line = (
                db.query(SourceInventory)
                .filter(SourceInventory.source_id == a.source_id, SourceInventory.resource == a.resource)
                .one_or_none()
            )
            if line is not None and line.allocated > line.available:
                candidates.append(a)
    else:
        candidates = []

    if not candidates:
        return None
    # Representative = highest priority_score (most urgent to fix first).
    return max(candidates, key=lambda a: a.priority_score)


def _reroute(db: Session, alloc: Allocation):
    config = get_or_create_config(db)
    weights = weights_from_config(config)
    now = time_now()

    requests, sources, vehicles, committed = converters.load_committed_snapshot(db)
    # Re-open exactly this allocation's share so the engine can replan it,
    # leaving every OTHER committed allocation's reservation intact.
    req_dto = next(r for r in requests if r.id == alloc.request_id)
    req_dto.allocated = max(0.0, req_dto.allocated - alloc.quantity)
    src_dto = next(s for s in sources if s.id == alloc.source_id)
    line = src_dto.line_for(alloc.resource)
    if line:
        line.allocated = max(0.0, line.allocated - alloc.quantity)
    veh_dto = next(v for v in vehicles if v.id == alloc.vehicle_id)
    if veh_dto.status != "Unavailable":
        veh_dto.trips = max(0, veh_dto.trips - 1)
        veh_dto.status = "Available"

    graph = converters.build_graph(db)
    single_request = replace(req_dto, required=alloc.quantity, allocated=0.0)
    results, unmet, _ = run_allocation([single_request], sources, vehicles, graph, weights, 1.0, now)
    return results, unmet


def trigger_replan(db: Session, trigger_type: str, target_id: str, description: str, value: float | None = None) -> ReplanEvent:
    if trigger_type not in TRIGGER_TO_SCENARIO_TYPE:
        raise ValueError(
            f"Unsupported trigger type for /replan: {trigger_type!r}. "
            "Use 'Road Blocked', 'Vehicle Unavailable' or 'Inventory Shortfall' "
            "(a brand-new request is better modeled via /scenario with 'Add Affected Area')."
        )

    metrics_before = compute_live_metrics(db)

    # Persist the real-world mutation immediately (this already happened).
    if trigger_type == "Road Blocked":
        edge = db.get(RoadEdge, target_id)
        if edge is None:
            raise LookupError(f"Road edge {target_id} not found")
        edge.condition = "BLOCKED"
        edge.blocked_reason = description
    elif trigger_type == "Vehicle Unavailable":
        vehicle = db.get(Vehicle, target_id)
        if vehicle is None:
            raise LookupError(f"Vehicle {target_id} not found")
        vehicle.status = "Unavailable"
    elif trigger_type == "Inventory Shortfall":
        factor = max(0.0, 1.0 - (value if value is not None else 30.0) / 100.0)
        lines = db.query(SourceInventory).filter(SourceInventory.source_id == target_id).all()
        if not lines:
            raise LookupError(f"Source {target_id} not found")
        for line in lines:
            line.available = round(line.available * factor, 2)
    db.commit()

    affected = db.query(Allocation).filter(Allocation.status.in_(("Accepted", "Modified"))).all()
    if trigger_type == "Road Blocked":
        affected_allocs = [a for a in affected if target_id in a.route_edge_ids]
    elif trigger_type == "Vehicle Unavailable":
        affected_allocs = [a for a in affected if a.vehicle_id == target_id]
    else:
        affected_allocs = [a for a in affected if a.source_id == target_id]
    affected_allocs = [a for a in affected_allocs if _active_delivery(db, a.id) is not None]
    affected_deliveries = [_active_delivery(db, a.id).id for a in affected_allocs]

    representative = _find_affected_committed_allocation(db, trigger_type, target_id)
    if representative is None:
        raise ValueError("No in-flight deliveries are affected by this change — nothing to replan")

    new_results, new_unmet = _reroute(db, representative)
    source_names = {s.id: s.name for s in converters.load_sources(db)}

    old_plan = {
        "sourceId": representative.source_id,
        "sourceName": source_names.get(representative.source_id, representative.source_id),
        "vehicleId": representative.vehicle_id,
        "routeId": f"RT-{representative.id}",
        "routeLabel": " → ".join(representative.route_edge_ids),
        "etaIso": _iso(representative.eta),
    }

    alternatives: list[str]
    if new_results:
        best = max(new_results, key=lambda r: r.quantity)
        new_plan = {
            "sourceId": best.source_id,
            "sourceName": best.source_name,
            "vehicleId": best.vehicle_id,
            "routeId": f"RT-NEW-{representative.id}",
            "routeLabel": " → ".join(best.route_edge_ids),
            "etaIso": _iso(best.eta),
        }
        alternatives = best.reasons
    else:
        # No feasible alternative — surface the original plan as 'new' too
        # (a no-op reroute) so the response always satisfies the
        # frontend's ReplanEvent contract, with the gap explained in text.
        best = None
        new_plan = dict(old_plan)
        alternatives = [
            f"No feasible reroute currently available for {representative.id} — all alternative "
            "sources/vehicles/routes are infeasible. Original plan retained; coordinator attention required."
        ]

    scenario_type = TRIGGER_TO_SCENARIO_TYPE.get(trigger_type)
    metrics_before_camel = _metrics_to_camel(metrics_before)
    metrics_after = metrics_before_camel
    if scenario_type:
        try:
            scn = simulate_scenario(
                db, [{"type": scenario_type, "target_id": target_id, "target_label": target_id, "value": value}]
            )
            metrics_after = {
                "demandFulfilledPct": scn.after.demand_fulfilled_pct,
                "criticalDemandFulfilledPct": scn.after.critical_demand_fulfilled_pct,
                "onTimeDeliveryPct": scn.after.on_time_delivery_pct,
                "totalDistanceKm": scn.after.total_distance_km,
                "vehicleTrips": scn.after.vehicle_trips,
                "unmetDemandUnits": scn.after.unmet_demand_units,
            }
        except (ValueError, LookupError):
            # The scenario preview couldn't run (e.g. an edge case in the
            # mutation) — fall back to "no measurable change" rather than
            # failing the whole replan, but keep the key casing consistent.
            metrics_after = metrics_before_camel

    event = ReplanEvent(
        id=next_id(db, ReplanEvent, "RPL"),
        triggered_at=time_now(),
        trigger_description=description,
        trigger_type=trigger_type,
        affected_delivery_ids=affected_deliveries,
        vehicles_affected_count=len({a.vehicle_id for a in affected_allocs}) or (1 if new_plan else 0),
        deadlines_at_risk_count=sum(1 for a in affected_allocs if not a.meets_deadline),
        old_plan=old_plan,
        new_plan=new_plan,
        alternatives_considered=alternatives,
        target_allocation_id=representative.id,
        new_source_id=new_plan["sourceId"],
        new_vehicle_id=new_plan["vehicleId"],
        new_route_node_ids=best.route_node_ids if best else representative.route_node_ids,
        new_route_edge_ids=best.route_edge_ids if best else representative.route_edge_ids,
        new_distance_km=best.distance_km if best else representative.distance_km,
        new_eta=best.eta if best else representative.eta,
        metrics_before=metrics_before_camel,
        metrics_after=metrics_after,
        status="Pending",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _active_delivery(db: Session, allocation_id: str) -> Delivery | None:
    d = db.query(Delivery).filter(Delivery.allocation_id == allocation_id).one_or_none()
    if d is not None and d.status != "Delivered":
        return d
    return None


def _iso(dt) -> str:
    from app.utils.time import iso

    return iso(dt)


def apply_replan(db: Session, replan_id: str) -> ReplanEvent:
    event = get_replan(db, replan_id)
    if event is None:
        raise LookupError(f"Replan event {replan_id} not found")
    if event.status != "Pending":
        return event
    if event.new_plan is None or event.target_allocation_id is None:
        raise ValueError("This replan has no feasible new plan to apply")

    alloc = db.get(Allocation, event.target_allocation_id)
    if alloc is None:
        raise LookupError(f"Allocation {event.target_allocation_id} not found")

    old_vehicle = db.get(Vehicle, alloc.vehicle_id)
    old_line = (
        db.query(SourceInventory)
        .filter(SourceInventory.source_id == alloc.source_id, SourceInventory.resource == alloc.resource)
        .one_or_none()
    )
    if old_line is not None:
        old_line.allocated = max(0.0, old_line.allocated - alloc.quantity)
    if old_vehicle is not None and old_vehicle.status != "Unavailable":
        old_vehicle.status = "Available"
        old_vehicle.current_delivery_id = None

    alloc.source_id = event.new_source_id
    alloc.vehicle_id = event.new_vehicle_id
    alloc.route_node_ids = event.new_route_node_ids or alloc.route_node_ids
    alloc.route_edge_ids = event.new_route_edge_ids or alloc.route_edge_ids
    alloc.distance_km = event.new_distance_km or alloc.distance_km
    alloc.eta = event.new_eta or alloc.eta
    alloc.meets_deadline = alloc.eta <= alloc.deadline
    alloc.reasons = [*alloc.reasons, f"Rerouted by replan {event.id}: {event.trigger_description}"]

    new_line = (
        db.query(SourceInventory)
        .filter(SourceInventory.source_id == alloc.source_id, SourceInventory.resource == alloc.resource)
        .one()
    )
    new_line.allocated += alloc.quantity
    new_vehicle = db.get(Vehicle, alloc.vehicle_id)
    if new_vehicle is not None:
        new_vehicle.status = "Assigned"

    delivery = db.query(Delivery).filter(Delivery.allocation_id == alloc.id).one_or_none()
    if delivery is not None:
        source = converters.load_sources(db)
        source_name = next((s.name for s in source if s.id == alloc.source_id), alloc.source_id)
        delivery.vehicle_id = alloc.vehicle_id
        delivery.source_id = alloc.source_id
        delivery.route_node_ids = alloc.route_node_ids
        delivery.route_edge_ids = alloc.route_edge_ids
        delivery.distance_km = alloc.distance_km
        delivery.origin_name = source_name
        delivery.eta = alloc.eta
        if new_vehicle is not None:
            new_vehicle.current_delivery_id = delivery.id

    event.status = "Applied"
    db.commit()
    record_snapshot(db, label="replan.apply")
    db.refresh(event)
    return event


def dismiss_replan(db: Session, replan_id: str) -> ReplanEvent:
    event = get_replan(db, replan_id)
    if event is None:
        raise LookupError(f"Replan event {replan_id} not found")
    if event.status == "Pending":
        event.status = "Dismissed"
        db.commit()
        db.refresh(event)
    return event
