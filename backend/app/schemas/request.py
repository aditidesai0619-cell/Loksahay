from __future__ import annotations

from app.models import AffectedRequest, RoadNode
from app.schemas.common import CamelModel, LatLng
from app.utils.time import iso


class AffectedRequestOut(CamelModel):
    id: str
    area_id: str
    area_name: str
    location: LatLng
    resource: str
    required: float
    unit: str
    allocated: float
    people_affected: int
    urgency: str
    deadline: str
    status: str
    reason: str | None = None
    alternative_source_name: str | None = None
    alternative_eta_iso: str | None = None
    created_at: str

    @staticmethod
    def from_model(row: AffectedRequest, node: RoadNode) -> "AffectedRequestOut":
        return AffectedRequestOut(
            id=row.id,
            areaId=row.area_id,
            areaName=row.area_name,
            location=LatLng(lat=node.lat, lng=node.lng),
            resource=row.resource,
            required=row.required,
            unit=row.unit,
            allocated=row.allocated,
            peopleAffected=row.people_affected,
            urgency=row.urgency,
            deadline=iso(row.deadline),
            status=row.status,
            reason=row.reason,
            alternativeSourceName=row.alternative_source_name,
            alternativeEtaIso=iso(row.alternative_eta) if row.alternative_eta else None,
            createdAt=iso(row.created_at),
        )
