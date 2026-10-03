from __future__ import annotations

from app.models import ReplanEvent
from app.schemas.common import CamelModel
from app.utils.time import iso


class ReplanPlanSnapshotOut(CamelModel):
    source_id: str
    source_name: str
    vehicle_id: str
    route_id: str
    route_label: str
    eta_iso: str


class ReplanEventOut(CamelModel):
    id: str
    triggered_at: str
    trigger_description: str
    trigger_type: str
    affected_delivery_ids: list[str]
    vehicles_affected_count: int
    deadlines_at_risk_count: int
    old_plan: ReplanPlanSnapshotOut
    new_plan: ReplanPlanSnapshotOut
    alternatives_considered: list[str]
    status: str
    metrics_before: dict | None = None
    metrics_after: dict | None = None

    @staticmethod
    def from_model(row: ReplanEvent) -> "ReplanEventOut":
        return ReplanEventOut(
            id=row.id,
            triggeredAt=iso(row.triggered_at),
            triggerDescription=row.trigger_description,
            triggerType=row.trigger_type,
            affectedDeliveryIds=row.affected_delivery_ids,
            vehiclesAffectedCount=row.vehicles_affected_count,
            deadlinesAtRiskCount=row.deadlines_at_risk_count,
            oldPlan=ReplanPlanSnapshotOut(**row.old_plan),
            newPlan=ReplanPlanSnapshotOut(**row.new_plan),
            alternativesConsidered=row.alternatives_considered,
            status=row.status,
            metricsBefore=row.metrics_before,
            metricsAfter=row.metrics_after,
        )
