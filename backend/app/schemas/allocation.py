from __future__ import annotations

from app.models import Allocation
from app.schemas.common import CamelModel
from app.utils.time import iso


class PriorityBreakdownOut(CamelModel):
    urgency_score: float
    population_need_score: float
    supply_deficit_score: float
    accessibility_score: float


class AllocationOut(CamelModel):
    id: str
    request_id: str
    source_id: str
    vehicle_id: str
    route_id: str
    resource: str
    quantity: float
    unit: str
    eta_iso: str
    deadline_iso: str
    status: str
    reasons: list[str]
    meets_deadline: bool
    priority_score: float
    priority_breakdown: PriorityBreakdownOut | None = None

    @staticmethod
    def from_model(row: Allocation) -> "AllocationOut":
        return AllocationOut(
            id=row.id,
            requestId=row.request_id,
            sourceId=row.source_id,
            vehicleId=row.vehicle_id,
            routeId=row.route_id,
            resource=row.resource,
            quantity=row.quantity,
            unit=row.unit,
            etaIso=iso(row.eta),
            deadlineIso=iso(row.deadline),
            status=row.status,
            reasons=row.reasons,
            meetsDeadline=row.meets_deadline,
            priorityScore=row.priority_score,
            priorityBreakdown=PriorityBreakdownOut(**row.priority_breakdown) if row.priority_breakdown else None,
        )
