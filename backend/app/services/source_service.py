from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import SupplySource


def list_sources(db: Session) -> list[SupplySource]:
    return db.query(SupplySource).order_by(SupplySource.id).all()


def get_source(db: Session, source_id: str) -> SupplySource | None:
    return db.get(SupplySource, source_id)
