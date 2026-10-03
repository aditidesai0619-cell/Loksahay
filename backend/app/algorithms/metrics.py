"""Shared metric computation for Analytics and Scenario comparisons.

Both the real LokSahay engine and the naive baseline engine produce the
same `AllocationResultDTO` / request-state shape, so one function can
score either of them identically ("calculate both methods using the same
dataset" — section 23).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.algorithms.dto import AllocationResultDTO, RequestDTO


@dataclass
class Metrics:
    demand_fulfilled_pct: float
    critical_demand_fulfilled_pct: float
    on_time_delivery_pct: float
    total_distance_km: float
    vehicle_trips: int
    unmet_demand_units: float


def compute_metrics(requests: list[RequestDTO], results: list[AllocationResultDTO]) -> Metrics:
    total_required = sum(r.required for r in requests) or 1.0
    total_allocated = sum(r.allocated for r in requests)

    critical = [r for r in requests if r.urgency == "Critical"]
    critical_required = sum(r.required for r in critical) or 1.0
    critical_allocated = sum(r.allocated for r in critical)

    on_time = sum(1 for res in results if res.meets_deadline)
    on_time_pct = round((on_time / len(results)) * 100, 1) if results else 100.0

    return Metrics(
        demand_fulfilled_pct=round((total_allocated / total_required) * 100, 1),
        critical_demand_fulfilled_pct=round((critical_allocated / critical_required) * 100, 1) if critical else 100.0,
        on_time_delivery_pct=on_time_pct,
        total_distance_km=round(sum(res.distance_km for res in results), 1),
        vehicle_trips=len(results),
        unmet_demand_units=round(sum(max(0.0, r.required - r.allocated) for r in requests), 1),
    )
