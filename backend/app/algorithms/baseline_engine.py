"""The 'simple baseline' comparison algorithm (section 23).

Nearest-source, first-come-first-served, single-source-only:
  - Requests are processed in `created_at` order (not by priority).
  - Each request is filled from whichever matching-resource source is
    GEOGRAPHICALLY NEAREST (by route distance, not ETA/deadline-aware).
  - No deadline check gates the allocation (a late delivery still counts
    as "allocated", it will just show up as not on-time).
  - No multi-source splitting and no minimum-coverage fairness pass — if
    the nearest source can't fully cover the request, the shortfall is
    simply left unmet rather than seeking a second source.
  - The first available vehicle with enough capacity is used.

This exists purely so Analytics can show a same-dataset, same-constraints
comparison against the real LokSahay engine — it is a deliberately naive
strategy, not a second "real" option.
"""

from __future__ import annotations

from datetime import datetime

from app.algorithms.dto import (
    AllocationResultDTO,
    RequestDTO,
    SourceDTO,
    UnmetDemandDTO,
    VehicleDTO,
    cargo_weight_kg,
)
from app.algorithms.allocation_engine import REASON_LABEL
from app.algorithms.graph import RoadGraph
from app.utils.time import minutes_from_now


def run_baseline_allocation(
    requests: list[RequestDTO],
    sources: list[SourceDTO],
    vehicles: list[VehicleDTO],
    graph: RoadGraph,
    now: datetime,
) -> tuple[list[AllocationResultDTO], list[UnmetDemandDTO]]:
    ordered = sorted(requests, key=lambda r: r.created_at)
    results: list[AllocationResultDTO] = []
    unmet: list[UnmetDemandDTO] = []

    for req in ordered:
        matching = [s for s in sources if s.line_for(req.resource) is not None and s.line_for(req.resource).remaining > 0]  # type: ignore[union-attr]

        best_source = None
        best_route = None
        best_distance = float("inf")
        for source in matching:
            route = graph.shortest_path(source.node_id, req.area_id)
            if route is None:
                continue
            if route.distance_km < best_distance:
                best_distance = route.distance_km
                best_source = source
                best_route = route

        if best_source is None or best_route is None:
            reason = "SOURCE_UNAVAILABLE" if not matching else "ROAD_BLOCKED"
            unmet.append(UnmetDemandDTO(req.id, req.required, 0.0, req.required, REASON_LABEL[reason]))
            continue

        line = best_source.line_for(req.resource)
        assert line is not None

        vehicle = next((v for v in vehicles if v.trips == 0 and v.status == "Available"), None)
        if vehicle is None:
            unmet.append(UnmetDemandDTO(req.id, req.required, 0.0, req.required, REASON_LABEL["NO_VEHICLE"]))
            continue

        unit_cap = vehicle.capacity_kg / max(cargo_weight_kg(req.resource, 1.0), 0.001)
        qty = min(req.required, line.remaining, unit_cap)
        if qty <= 0:
            unmet.append(UnmetDemandDTO(req.id, req.required, 0.0, req.required, REASON_LABEL["NO_VEHICLE"]))
            continue

        line.allocated += qty
        vehicle.trips += 1  # baseline never reuses a vehicle for a second trip
        req.allocated += qty
        eta = minutes_from_now(best_route.travel_time_min, now)

        results.append(
            AllocationResultDTO(
                request_id=req.id,
                source_id=best_source.id,
                source_name=best_source.name,
                source_verified=best_source.verified,
                vehicle_id=vehicle.id,
                resource=req.resource,
                quantity=round(qty, 2),
                unit=req.unit,
                route_node_ids=best_route.node_ids,
                route_edge_ids=best_route.edge_ids,
                distance_km=best_route.distance_km,
                eta_minutes=best_route.travel_time_min,
                eta=eta,
                deadline=req.deadline,
                meets_deadline=eta <= req.deadline,
                priority_score=0.0,
                reasons=["Nearest available source (baseline: first-come, nearest-source, single-source only)"],
            )
        )

        if req.unmet > 0.01:
            unmet.append(UnmetDemandDTO(req.id, req.required, req.allocated, req.unmet, REASON_LABEL["INSUFFICIENT_INVENTORY"]))

    return results, unmet
