from __future__ import annotations

from app.models import RoadEdge, RoadNode
from app.schemas.common import CamelModel, LatLng

CONDITION_TO_FRONTEND = {"OPEN": "Clear", "DEGRADED": "Degraded", "BLOCKED": "Blocked"}
CONDITION_FROM_FRONTEND = {v: k for k, v in CONDITION_TO_FRONTEND.items()}


class RoadNodeOut(CamelModel):
    id: str
    name: str
    location: LatLng

    @staticmethod
    def from_model(row: RoadNode) -> "RoadNodeOut":
        return RoadNodeOut(id=row.id, name=row.name, location=LatLng(lat=row.lat, lng=row.lng))


class RoadEdgeOut(CamelModel):
    id: str
    from_: str
    to: str
    distance_km: float
    condition: str
    blocked_reason: str | None = None

    @staticmethod
    def from_model(row: RoadEdge) -> "RoadEdgeOut":
        return RoadEdgeOut(
            id=row.id,
            from_=row.from_node_id,
            to=row.to_node_id,
            distanceKm=row.distance_km,
            condition=CONDITION_TO_FRONTEND.get(row.condition, row.condition),
            blockedReason=row.blocked_reason,
        )
