"""Scenario simulation & application (section 22).

Both 'before' and 'after' are computed by running the SAME allocation
engine, starting from the SAME committed-allocations baseline (so the
comparison isolates exactly the effect of the hypothetical change):

  before = committed allocations + a fresh engine fill of remaining open
           demand, under TODAY's real network/inventory/fleet.
  after  = committed allocations + a fresh engine fill of remaining open
           demand, under the SAME state with the scenario's hypothetical
           change(s) applied.

`simulate_scenario` never touches the database. `apply_scenario` performs
the same computation and then persists the mutation (road condition,
vehicle status, inventory, new request, urgency) and re-runs
`run_allocation_and_persist` for real.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.algorithms.allocation_engine import run_allocation
from app.algorithms.bottlenecks import BottleneckDTO, detect_bottlenecks
from app.algorithms.dto import AllocationResultDTO, RequestDTO, clone_requests, clone_sources, clone_vehicles
from app.algorithms.graph import RoadGraph
from app.algorithms.metrics import Metrics, compute_metrics
from app.algorithms.scenario_mutations import ScenarioActionInput, apply_action
from app.models import AffectedRequest, RoadEdge, SourceInventory, Vehicle
from app.services import converters
from app.services.config_service import get_or_create_config, weights_from_config
from app.utils.time import now as time_now


@dataclass
class ScenarioResult:
    id: str
    actions: list[ScenarioActionInput]
    before: Metrics
    after: Metrics
    changed_allocations: int
    changed_routes: int
    affected_delivery_ids: list[str]
    new_bottlenecks: list[BottleneckDTO]
    generated_at: datetime


def _fresh_fill(requests, sources, vehicles, graph, weights, min_coverage, now):
    return run_allocation(requests, sources, vehicles, graph, weights, min_coverage, now)


def _index_by_request(results: list[AllocationResultDTO]) -> dict[str, list[AllocationResultDTO]]:
    out: dict[str, list[AllocationResultDTO]] = {}
    for r in results:
        out.setdefault(r.request_id, []).append(r)
    return out


def _diff_results(before_new: list[AllocationResultDTO], after_new: list[AllocationResultDTO]) -> tuple[int, int]:
    before_by_req = _index_by_request(before_new)
    after_by_req = _index_by_request(after_new)
    all_request_ids = set(before_by_req) | set(after_by_req)

    changed_allocations = 0
    changed_routes = 0
    for rid in all_request_ids:
        b = sorted(((r.source_id, r.vehicle_id, round(r.quantity, 1)) for r in before_by_req.get(rid, [])))
        a = sorted(((r.source_id, r.vehicle_id, round(r.quantity, 1)) for r in after_by_req.get(rid, [])))
        if b != a:
            changed_allocations += 1
        b_routes = sorted((tuple(r.route_edge_ids) for r in before_by_req.get(rid, [])))
        a_routes = sorted((tuple(r.route_edge_ids) for r in after_by_req.get(rid, [])))
        if b_routes != a_routes:
            changed_routes += 1
    return changed_allocations, changed_routes


def _run_both_branches(
    db: Session, actions: list[ScenarioActionInput]
) -> tuple[Metrics, Metrics, list[AllocationResultDTO], list[AllocationResultDTO], list[RequestDTO], list]:
    config = get_or_create_config(db)
    weights = weights_from_config(config)
    now = time_now()

    base_requests, base_sources, base_vehicles, committed = converters.load_committed_snapshot(db)
    nodes = converters.load_nodes(db)
    base_edges = converters.load_edges(db)

    source_by_id = {s.id: s for s in base_sources}
    committed_results = [
        converters.allocation_to_result_dto(a, source_by_id[a.source_id].name, source_by_id[a.source_id].verified)
        for a in committed
    ]

    # BEFORE branch: today's real conditions.
    before_requests = clone_requests(base_requests)
    before_sources = clone_sources(base_sources)
    before_vehicles = clone_vehicles(base_vehicles)
    before_graph = RoadGraph(nodes, [e for e in base_edges])
    before_new, before_unmet, _ = _fresh_fill(
        before_requests, before_sources, before_vehicles, before_graph, weights, config.minimum_coverage_pct, now
    )

    # AFTER branch: same starting point, with the scenario applied.
    after_requests = clone_requests(base_requests)
    after_sources = clone_sources(base_sources)
    after_vehicles = clone_vehicles(base_vehicles)
    after_edges = [
        type(e)(id=e.id, from_id=e.from_id, to_id=e.to_id, distance_km=e.distance_km, condition=e.condition, blocked_reason=e.blocked_reason)
        for e in base_edges
    ]
    for action in actions:
        apply_action(action, after_requests, after_sources, after_vehicles, after_edges, now)
    after_graph = RoadGraph(nodes, after_edges)
    after_new, after_unmet, _ = _fresh_fill(
        after_requests, after_sources, after_vehicles, after_graph, weights, config.minimum_coverage_pct, now
    )

    before_metrics = compute_metrics(before_requests, committed_results + before_new)
    after_metrics = compute_metrics(after_requests, committed_results + after_new)

    return before_metrics, after_metrics, before_new, after_new, after_requests, after_unmet


def simulate_scenario(db: Session, raw_actions: list[dict]) -> ScenarioResult:
    actions = [ScenarioActionInput(**a) for a in raw_actions]
    before_metrics, after_metrics, before_new, after_new, after_requests, after_unmet = _run_both_branches(db, actions)

    changed_allocations, changed_routes = _diff_results(before_new, after_new)

    blocked_edge_ids = {a.target_id for a in actions if a.type == "Block Road"}
    removed_vehicle_ids = {a.target_id for a in actions if a.type == "Remove Vehicle"}
    affected_delivery_ids = _affected_delivery_ids(db, blocked_edge_ids, removed_vehicle_ids)

    requests_by_id = {r.id: r for r in after_requests}
    after_sources = converters.load_sources(db)
    after_vehicles = converters.load_vehicles(db)
    new_bottlenecks = detect_bottlenecks(requests_by_id, after_unmet, after_sources, after_vehicles)

    return ScenarioResult(
        id=f"SCN-{int(time.time() * 1000)}",
        actions=actions,
        before=before_metrics,
        after=after_metrics,
        changed_allocations=changed_allocations,
        changed_routes=changed_routes,
        affected_delivery_ids=affected_delivery_ids,
        new_bottlenecks=new_bottlenecks,
        generated_at=time_now(),
    )


def _affected_delivery_ids(db: Session, blocked_edge_ids: set[str], removed_vehicle_ids: set[str]) -> list[str]:
    from app.models import Delivery

    if not blocked_edge_ids and not removed_vehicle_ids:
        return []
    affected = []
    for d in db.query(Delivery).filter(Delivery.status != "Delivered").all():
        if blocked_edge_ids & set(d.route_edge_ids):
            affected.append(d.id)
        elif d.vehicle_id in removed_vehicle_ids:
            affected.append(d.id)
    return affected


def apply_scenario(db: Session, raw_actions: list[dict]) -> ScenarioResult:
    """Persist the scenario's mutations for real, then re-run the live
    allocation engine so the new plan is actually committed."""
    actions = [ScenarioActionInput(**a) for a in raw_actions]
    result = simulate_scenario(db, raw_actions)

    now = time_now()
    for action in actions:
        if action.type == "Block Road":
            edge = db.get(RoadEdge, action.target_id)
            if edge is not None:
                edge.condition = "BLOCKED"
                edge.blocked_reason = edge.blocked_reason or "Blocked (scenario applied)"
        elif action.type == "Remove Vehicle":
            vehicle = db.get(Vehicle, action.target_id)
            if vehicle is not None:
                vehicle.status = "Unavailable"
        elif action.type == "Reduce Inventory":
            factor = max(0.0, 1.0 - (action.value if action.value is not None else 30.0) / 100.0)
            for line in db.query(SourceInventory).filter(SourceInventory.source_id == action.target_id).all():
                line.available = round(line.available * factor, 2)
        elif action.type == "Add Affected Area":
            from app.algorithms.scenario_mutations import NEW_REQUEST_DEFAULTS
            from app.utils.ids import next_id
            from app.utils.time import minutes_from_now

            db.add(
                AffectedRequest(
                    id=next_id(db, AffectedRequest, "REQ"),
                    area_id=action.target_id,
                    area_name=action.target_label,
                    resource=NEW_REQUEST_DEFAULTS["resource"],
                    required=NEW_REQUEST_DEFAULTS["required"],
                    unit=NEW_REQUEST_DEFAULTS["unit"],
                    allocated=0,
                    people_affected=int(NEW_REQUEST_DEFAULTS["people_affected"]),
                    urgency="High",
                    deadline=minutes_from_now(180, now),
                    status="Unfulfilled",
                    created_at=now,
                )
            )
        elif action.type == "Increase Urgency":
            from app.algorithms.scenario_mutations import URGENCY_LADDER

            req = db.get(AffectedRequest, action.target_id)
            if req is not None:
                idx = URGENCY_LADDER.index(req.urgency) if req.urgency in URGENCY_LADDER else 0
                req.urgency = URGENCY_LADDER[min(idx + 1, len(URGENCY_LADDER) - 1)]
    db.commit()

    from app.services.allocation_service import run_allocation_and_persist

    run_allocation_and_persist(db, snapshot_label="scenario.apply")
    return result
