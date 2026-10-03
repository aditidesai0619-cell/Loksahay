from __future__ import annotations

from app.algorithms.metrics import Metrics
from app.schemas.bottleneck import BottleneckOut
from app.schemas.common import CamelModel
from app.utils.time import iso


class ScenarioActionIn(CamelModel):
    id: str = "ACT-1"
    type: str
    target_id: str
    target_label: str = ""
    value: float | None = None


class ScenarioMetricsOut(CamelModel):
    demand_fulfilled_pct: float
    critical_demand_fulfilled_pct: float
    on_time_delivery_pct: float
    total_distance_km: float
    vehicle_trips: int
    unmet_demand_units: float

    @staticmethod
    def from_metrics(m: Metrics) -> "ScenarioMetricsOut":
        return ScenarioMetricsOut(
            demandFulfilledPct=m.demand_fulfilled_pct,
            criticalDemandFulfilledPct=m.critical_demand_fulfilled_pct,
            onTimeDeliveryPct=m.on_time_delivery_pct,
            totalDistanceKm=m.total_distance_km,
            vehicleTrips=m.vehicle_trips,
            unmetDemandUnits=m.unmet_demand_units,
        )


class ScenarioResultOut(CamelModel):
    id: str
    before: ScenarioMetricsOut
    after: ScenarioMetricsOut
    changed_allocations: int
    changed_routes: int
    affected_delivery_ids: list[str]
    new_bottlenecks: list[BottleneckOut]
    generated_at: str

    @staticmethod
    def from_result(result) -> "ScenarioResultOut":
        return ScenarioResultOut(
            id=result.id,
            before=ScenarioMetricsOut.from_metrics(result.before),
            after=ScenarioMetricsOut.from_metrics(result.after),
            changedAllocations=result.changed_allocations,
            changedRoutes=result.changed_routes,
            affectedDeliveryIds=result.affected_delivery_ids,
            newBottlenecks=[BottleneckOut.from_dto(b) for b in result.new_bottlenecks],
            generatedAt=iso(result.generated_at),
        )
