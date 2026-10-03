from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AffectedRequest


def list_requests(db: Session) -> list[AffectedRequest]:
    return db.query(AffectedRequest).order_by(AffectedRequest.id).all()


def get_request(db: Session, request_id: str) -> AffectedRequest | None:
    return db.get(AffectedRequest, request_id)
