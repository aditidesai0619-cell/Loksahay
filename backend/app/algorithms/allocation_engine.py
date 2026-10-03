"""The greedy + fairness allocation engine (sections 12 & 13).

This is the primary LokSahay allocation paradigm: GREEDY, over a GRAPH
(the road network) for route feasibility/ETA.

High-level algorithm:

  1. Compute a priority score for every request (priority.py).
  2. PASS 1 — minimum feasible coverage (fairness): process requests in
     priority order, but cap each request's target at
     `minimum_coverage_pct * required`. This guarantees that a feasible
     but low-priority request still gets *something* before high-priority
     requests are allowed to exhaust shared inventory/vehicles in pass 2.
     (Within pass 1 itself we still process by priority order as a
     tie-break for when even minimum coverage can't be given to everyone —
     but because EVERY request gets a capped attempt before ANY request
     is topped up further, lower-priority areas are never zeroed out by
     higher-priority ones as long as minimum coverage was feasible.)
  3. PASS 2 — priority top-up: process the same priority order again,
     this time with an uncapped target (remaining `required`), consuming
     whatever inventory/vehicles pass 1 left.
  4. Whatever is still unmet after both passes is returned with a
     classified reason and (where one exists) an alternative suggestion.

For each allocation attempt, a request may draw from MULTIPLE sources
(multi-source splitting) — the inner loop keeps picking the best
remaining candidate until the target quantity is met or no more feasible
candidates exist.

Complexity (see also `docs`/final report):
  - Priority computation + sort: O(D log D)
  - Candidate evaluation per allocation step: O(S x V), repeated up to
    ~O(S) times per request in the worst case (one source exhausted per
    step) => O(D x S x V) for vehicle/inventory evaluation.
  - Each candidate source requires one Dijkstra call: O(E log N).
    Worst case total routing cost: O(D x S x E log N).
  - Overall: O(D log D + D×S×V + D×S×E log N)
  - Space: O(N + E + D + S + V) for the graph + working DTOs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.algorithms.dto import (
    AllocationResultDTO,
    PriorityBreakdownDTO,
    RequestDTO,
    SourceDTO,
    UnmetDemandDTO,
    VehicleDTO,
    cargo_weight_kg,
)
from app.algorithms.graph import RoadGraph
from app.algorithms.priority import PriorityWeights, compute_priorities
from app.utils.time import minutes_from_now

REASON_LABEL = {
    "INSUFFICIENT_INVENTORY": "Insufficient inventory",
    "NO_VEHICLE": "No feasible vehicle",
    "NO_FEASIBLE_ROUTE": "Road inaccessible",
    "ROAD_BLOCKED": "Road inaccessible",
    "DEADLINE_INFEASIBLE": "Deadline infeasible",
    "SOURCE_UNAVAILABLE": "Source unavailable",
}
# Deterministic tie-break order when multiple rejection codes were seen
# for the same request and we must pick one dominant reason.
#  prototype simplification: a vehicle may be scheduled for up to this
# many sequential trips within a single planning pass (it is dispatched,
# returns, and is dispatched again) rather than one-trip-per-run-forever.
# This keeps a small demo fleet (5-8 vehicles) from artificially starving
# lower-priority requests of vehicle capacity even when inventory and
# routes remain feasible for them.
MAX_TRIPS_PER_VEHICLE_PER_RUN = 2

REASON_PRIORITY = [
    "SOURCE_UNAVAILABLE",
    "ROAD_BLOCKED",
    "NO_FEASIBLE_ROUTE",
    "DEADLINE_INFEASIBLE",
    "NO_VEHICLE",
    "INSUFFICIENT_INVENTORY",
]


@dataclass
class _Rejection:
    source_id: str
    source_name: str
    code: str
    detail: str


@dataclass
class _Candidate:
    source: SourceDTO
    vehicle: VehicleDTO
    route_node_ids: list[str]
    route_edge_ids: list[str]
    distance_km: float
    travel_time_min: float
    eta: datetime
    quantity: float


def _find_candidates(
    req: RequestDTO,
    target_qty: float,
    sources: list[SourceDTO],
    vehicles: list[VehicleDTO],
    graph: RoadGraph,
    now: datetime,
    rejections: list[_Rejection],
) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    available_vehicles = [
        v for v in vehicles if v.trips < MAX_TRIPS_PER_VEHICLE_PER_RUN and v.status == "Available"
    ]

    matching_sources = [s for s in sources if s.line_for(req.resource) is not None]

    for source in matching_sources:
        line = source.line_for(req.resource)
        if line is None or line.remaining <= 0:
            rejections.append(
                _Rejection(source.id, source.name, "INSUFFICIENT_INVENTORY", f"{source.name} has no remaining {req.resource} inventory")
            )
            continue

        route = graph.shortest_path(source.node_id, req.area_id)
        if route is None:
            rejections.append(
                _Rejection(source.id, source.name, "ROAD_BLOCKED", f"No open road path from {source.name} to {req.area_name}")
            )
            continue

        eta = minutes_from_now(route.travel_time_min, now)
        if eta > req.deadline:
            rejections.append(
                _Rejection(
                    source.id,
                    source.name,
                    "DEADLINE_INFEASIBLE",
                    f"Route ETA from {source.name} ({route.travel_time_min:.0f} min) exceeds deadline",
                )
            )
            continue

        best_vehicle = None
        best_qty = 0.0
        for vehicle in available_vehicles:
            unit_cap = vehicle.capacity_kg / max(cargo_weight_kg(req.resource, 1.0), 0.001)
            qty = min(target_qty, line.remaining, unit_cap)
            if qty > best_qty:
                best_qty = qty
                best_vehicle = vehicle

        if best_vehicle is None or best_qty <= 0:
            rejections.append(
                _Rejection(source.id, source.name, "NO_VEHICLE", f"No available vehicle has capacity for a {req.resource} shipment from {source.name}")
            )
            continue

        candidates.append(
            _Candidate(
                source=source,
                vehicle=best_vehicle,
                route_node_ids=route.node_ids,
                route_edge_ids=route.edge_ids,
                distance_km=route.distance_km,
                travel_time_min=route.travel_time_min,
                eta=eta,
                quantity=best_qty,
            )
        )
    return candidates


def _choose_best(candidates: list[_Candidate]) -> _Candidate:
    # Prefer verified sources, then larger deliverable quantity, then
    # shorter ETA (section 14: do NOT simply pick nearest source).
    return sorted(
        candidates,
        key=lambda c: (not c.source.verified, -c.quantity, c.travel_time_min),
    )[0]


def _allocate_for_request(
    req: RequestDTO,
    target_qty: float,
    sources: list[SourceDTO],
    vehicles: list[VehicleDTO],
    graph: RoadGraph,
    now: datetime,
    priority_score: float,
) -> list[AllocationResultDTO]:
    results: list[AllocationResultDTO] = []
    remaining_target = min(target_qty, req.unmet)
    rejections: list[_Rejection] = []

    while remaining_target > 0.01:
        candidates = _find_candidates(req, remaining_target, sources, vehicles, graph, now, rejections)
        if not candidates:
            break
        chosen = _choose_best(candidates)

        line = chosen.source.line_for(req.resource)
        assert line is not None
        line.allocated += chosen.quantity
        chosen.vehicle.trips += 1
        req.allocated += chosen.quantity
        remaining_target -= chosen.quantity

        rejected_alternatives = [r for r in rejections if r.source_id != chosen.source.id]
        reasons = [
            f"{req.urgency} urgency request (priority score {priority_score:.2f})",
            f"{chosen.source.name} {'is a verified source' if chosen.source.verified else 'is an unverified but usable source'} "
            f"with {line.remaining + chosen.quantity:g} {req.unit} {req.resource} remaining before this allocation",
            f"Vehicle {chosen.vehicle.id} ({chosen.vehicle.type}, {chosen.vehicle.capacity_kg:g} kg capacity) can carry the shipment",
            f"Route {' → '.join(chosen.route_edge_ids) or '(same node)'} is feasible — {chosen.distance_km:g} km, ETA {chosen.travel_time_min:.0f} min",
            f"ETA meets the deadline" if chosen.eta <= req.deadline else "ETA exceeds deadline — flagged infeasible",
        ]
        if rejected_alternatives:
            for rej in rejected_alternatives[:2]:
                reasons.append(f"Rejected {rej.source_name}: {rej.detail}")

        results.append(
            AllocationResultDTO(
                request_id=req.id,
                source_id=chosen.source.id,
                source_name=chosen.source.name,
                source_verified=chosen.source.verified,
                vehicle_id=chosen.vehicle.id,
                resource=req.resource,
                quantity=round(chosen.quantity, 2),
                unit=req.unit,
                route_node_ids=chosen.route_node_ids,
                route_edge_ids=chosen.route_edge_ids,
                distance_km=chosen.distance_km,
                eta_minutes=chosen.travel_time_min,
                eta=chosen.eta,
                deadline=req.deadline,
                meets_deadline=chosen.eta <= req.deadline,
                priority_score=priority_score,
                reasons=reasons,
            )
        )
        rejections = []  # candidates re-evaluated fresh next loop

    return results


def _classify_unmet_reason(
    req: RequestDTO, sources: list[SourceDTO], vehicles: list[VehicleDTO], graph: RoadGraph, now: datetime
) -> str:
    matching = [s for s in sources if s.line_for(req.resource) is not None]
    if not matching:
        return "SOURCE_UNAVAILABLE"

    any_route = False
    any_route_on_time = False
    any_stock = False
    for s in matching:
        line = s.line_for(req.resource)
        if line and line.remaining > 0:
            any_stock = True
        route = graph.shortest_path(s.node_id, req.area_id)
        if route is not None:
            any_route = True
            if minutes_from_now(route.travel_time_min, now) <= req.deadline:
                any_route_on_time = True

    if not any_route:
        return "ROAD_BLOCKED"
    if not any_route_on_time:
        return "DEADLINE_INFEASIBLE"
    if not any_stock:
        return "INSUFFICIENT_INVENTORY"

    # Stock and a feasible on-time route both exist somewhere — if the
    # fleet is nonetheless fully committed (every vehicle at its trip
    # cap, or unavailable), the TRUE bottleneck was vehicle capacity, not
    # inventory. This is checked last since it is a network-wide fact,
    # not specific to this one request's candidate sources.
    any_vehicle_free = any(v.status == "Available" and v.trips < MAX_TRIPS_PER_VEHICLE_PER_RUN for v in vehicles)
    if not any_vehicle_free:
        return "NO_VEHICLE"

    return "INSUFFICIENT_INVENTORY"


def run_allocation(
    requests: list[RequestDTO],
    sources: list[SourceDTO],
    vehicles: list[VehicleDTO],
    graph: RoadGraph,
    weights: PriorityWeights,
    minimum_coverage_pct: float,
    now: datetime,
) -> tuple[list[AllocationResultDTO], list[UnmetDemandDTO], dict[str, PriorityBreakdownDTO]]:
    priorities = compute_priorities(requests, sources, graph, weights)
    ordered = sorted(requests, key=lambda r: priorities[r.id].priority_score, reverse=True)

    all_results: list[AllocationResultDTO] = []

    # PASS 1 — minimum feasible coverage.
    for req in ordered:
        if req.unmet <= 0:
            continue
        cap_target = req.required * minimum_coverage_pct
        target = max(0.0, min(cap_target, req.unmet))
        if target <= 0:
            continue
        all_results.extend(
            _allocate_for_request(req, target, sources, vehicles, graph, now, priorities[req.id].priority_score)
        )

    # PASS 2 — priority-ordered top-up with whatever remains.
    for req in ordered:
        if req.unmet <= 0:
            continue
        all_results.extend(
            _allocate_for_request(req, req.unmet, sources, vehicles, graph, now, priorities[req.id].priority_score)
        )

    unmet: list[UnmetDemandDTO] = []
    for req in ordered:
        if req.unmet <= 0.01:
            continue
        code = _classify_unmet_reason(req, sources, vehicles, graph, now)
        alt_name, alt_eta = _best_alternative(req, sources, graph, now)
        unmet.append(
            UnmetDemandDTO(
                request_id=req.id,
                required=req.required,
                allocated=req.allocated,
                unmet=req.unmet,
                reason=REASON_LABEL[code],
                alternative_source_name=alt_name,
                alternative_eta=alt_eta,
            )
        )

    return all_results, unmet, priorities


def _best_alternative(
    req: RequestDTO, sources: list[SourceDTO], graph: RoadGraph, now: datetime
) -> tuple[str | None, datetime | None]:
    """Best remaining candidate for a still-unmet request, REGARDLESS of
    whether it would meet the deadline or has enough stock — this is the
    'alternative source + alternative ETA' the frontend's unmet-demand
    panel surfaces (section 19), i.e. the closest thing to a feasible
    option even when none fully qualifies."""
    best: tuple[str, datetime] | None = None
    best_time = float("inf")
    for source in sources:
        if source.line_for(req.resource) is None:
            continue
        route = graph.shortest_path(source.node_id, req.area_id)
        if route is None:
            continue
        if route.travel_time_min < best_time:
            best_time = route.travel_time_min
            best = (source.name, minutes_from_now(route.travel_time_min, now))
    return best if best else (None, None)
