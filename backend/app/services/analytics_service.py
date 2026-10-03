"""Analytics (section 23).

`current` reflects the REAL persisted state. `loksahay` and `baseline`
are both FRESH runs of their respective algorithms over the SAME
full-capacity snapshot (today's real road network, but ignoring any
already-committed allocations) — "calculate both methods using the same
dataset," not a live-state-vs-hypothetical comparison. No performance
numbers are hardcoded; both are computed from the current request/source/
vehicle/road rows every time this endpoint is called.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.algorithms.allocation_engine import run_allocation
from app.algorithms.baseline_engine import run_baseline_allocation
from app.algorithms.dto import clone_requests, clone_sources, clone_vehicles
from app.algorithms.metrics import Metrics, compute_metrics
from app.models import PlanSnapshot
from app.services import converters
from app.services.config_service import get_or_create_config, weights_from_config
from app.services.plan_snapshot_service import compute_live_metrics
from app.utils.time import iso, now as time_now


@dataclass
class AlgorithmComparison:
    label: str
    metrics: Metrics


@dataclass
class HistoryPoint:
    timestamp: str
    demand_fulfilled_pct: float
    on_time_delivery_pct: float


@dataclass
class AnalyticsResult:
    current: Metrics
    loksahay: AlgorithmComparison
    baseline: AlgorithmComparison
    history: list[HistoryPoint]


def get_analytics(db: Session) -> AnalyticsResult:
    live = compute_live_metrics(db)
    current = Metrics(
        demand_fulfilled_pct=live["demand_fulfilled_pct"],
        critical_demand_fulfilled_pct=live["critical_demand_fulfilled_pct"],
        on_time_delivery_pct=live["on_time_delivery_pct"],
        total_distance_km=live["total_distance_km"],
        vehicle_trips=live["vehicle_trips"],
        unmet_demand_units=live["unmet_demand_units"],
    )

    config = get_or_create_config(db)
    weights = weights_from_config(config)
    now = time_now()

    base_requests = converters.load_requests(db, reset_allocated=True)
    base_sources = converters.load_sources(db, reset_allocated=True)
    base_vehicles = converters.load_vehicles(db, reset_assignments=True)
    graph = converters.build_graph(db)

    ls_requests, ls_sources, ls_vehicles = (
        clone_requests(base_requests),
        clone_sources(base_sources),
        clone_vehicles(base_vehicles),
    )
    ls_results, _, _ = run_allocation(ls_requests, ls_sources, ls_vehicles, graph, weights, config.minimum_coverage_pct, now)
    loksahay_metrics = compute_metrics(ls_requests, ls_results)

    bl_requests, bl_sources, bl_vehicles = (
        clone_requests(base_requests),
        clone_sources(base_sources),
        clone_vehicles(base_vehicles),
    )
    bl_results, _ = run_baseline_allocation(bl_requests, bl_sources, bl_vehicles, graph, now)
    baseline_metrics = compute_metrics(bl_requests, bl_results)

    history_rows = db.query(PlanSnapshot).order_by(PlanSnapshot.timestamp).all()
    history = [
        HistoryPoint(
            timestamp=iso(row.timestamp),
            demand_fulfilled_pct=row.demand_fulfilled_pct,
            on_time_delivery_pct=row.on_time_delivery_pct,
        )
        for row in history_rows
    ]

    return AnalyticsResult(
        current=current,
        loksahay=AlgorithmComparison(label="LokSahay Allocation", metrics=loksahay_metrics),
        baseline=AlgorithmComparison(label="Simple Baseline (nearest-source / first-come)", metrics=baseline_metrics),
        history=history,
    )
