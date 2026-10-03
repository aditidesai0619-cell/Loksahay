from __future__ import annotations

from sqlalchemy.orm import Session

from app.algorithms.bottlenecks import BottleneckDTO, detect_bottlenecks
from app.algorithms.dto import UnmetDemandDTO
from app.models import AffectedRequest
from app.services import converters


def compute_bottlenecks(db: Session) -> list[BottleneckDTO]:
    requests = converters.load_requests(db)
    sources = converters.load_sources(db)
    vehicles = converters.load_vehicles(db)
    requests_by_id = {r.id: r for r in requests}

    rows = db.query(AffectedRequest).filter(AffectedRequest.status != "Fulfilled").all()
    unmet = [
        UnmetDemandDTO(
            request_id=row.id,
            required=row.required,
            allocated=row.allocated,
            unmet=row.required - row.allocated,
            reason=row.reason or "Insufficient inventory",
        )
        for row in rows
        if row.required - row.allocated > 0.01
    ]
    return detect_bottlenecks(requests_by_id, unmet, sources, vehicles)
