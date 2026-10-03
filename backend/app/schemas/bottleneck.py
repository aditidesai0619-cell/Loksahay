from __future__ import annotations

from app.algorithms.bottlenecks import BottleneckDTO
from app.schemas.common import CamelModel


class BottleneckOut(CamelModel):
    id: str
    type: str
    impact: str
    affected_request_ids: list[str]
    suggested_action: str

    @staticmethod
    def from_dto(b: BottleneckDTO) -> "BottleneckOut":
        return BottleneckOut(
            id=b.id,
            type=b.type,
            impact=b.impact,
            affectedRequestIds=b.affected_request_ids,
            suggestedAction=b.suggested_action,
        )
