from __future__ import annotations

from app.schemas.common import CamelModel, LatLng
from app.services import system_service
from app.utils.time import iso


class PriorityWeightsOut(CamelModel):
    urgency: float
    population_need: float
    supply_deficit: float
    accessibility: float


class OperationalSummaryOut(CamelModel):
    region: str
    system_status: str
    last_plan_generated_at: str | None
    critical_needs: int
    active_deliveries: int
    resource_coverage_pct: float
    vehicles_available: int
    at_risk_deliveries: int

    @staticmethod
    def from_dto(s: system_service.OperationalSummary) -> "OperationalSummaryOut":
        return OperationalSummaryOut(
            region=s.region,
            systemStatus=s.system_status,
            lastPlanGeneratedAt=iso(s.last_plan_generated_at) if s.last_plan_generated_at else None,
            criticalNeeds=s.critical_needs,
            activeDeliveries=s.active_deliveries,
            resourceCoveragePct=s.resource_coverage_pct,
            vehiclesAvailable=s.vehicles_available,
            atRiskDeliveries=s.at_risk_deliveries,
        )


class AlgorithmSnapshotOut(CamelModel):
    requests_evaluated: int
    verified_sources: int
    available_vehicles: int
    feasible_routes: int
    minimum_coverage_pct: float
    plan_generated_at: str | None
    priority_weights: PriorityWeightsOut

    @staticmethod
    def from_dto(s: system_service.AlgorithmSnapshot) -> "AlgorithmSnapshotOut":
        return AlgorithmSnapshotOut(
            requestsEvaluated=s.requests_evaluated,
            verifiedSources=s.verified_sources,
            availableVehicles=s.available_vehicles,
            feasibleRoutes=s.feasible_routes,
            minimumCoveragePct=s.minimum_coverage_pct,
            planGeneratedAt=iso(s.plan_generated_at) if s.plan_generated_at else None,
            priorityWeights=PriorityWeightsOut(
                urgency=s.priority_weights.urgency,
                populationNeed=s.priority_weights.population_need,
                supplyDeficit=s.priority_weights.supply_deficit,
                accessibility=s.priority_weights.accessibility,
            ),
        )


class CoordinatorOut(CamelModel):
    name: str
    role: str
    region: str
    initials: str

    @staticmethod
    def from_dto(c: system_service.Coordinator) -> "CoordinatorOut":
        return CoordinatorOut(name=c.name, role=c.role, region=c.region, initials=c.initials)


class RegionMetaOut(CamelModel):
    region: str
    center: LatLng
    zoom: int
