from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import RoadNode
from app.schemas.source import SupplySourceOut
from app.services import source_service

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SupplySourceOut])
def list_sources(db: Session = Depends(get_db)):
    rows = source_service.list_sources(db)
    nodes = {n.id: n for n in db.query(RoadNode).all()}
    return [SupplySourceOut.from_model(r, nodes[r.node_id]) for r in rows]


@router.get("/{source_id}", response_model=SupplySourceOut)
def get_source(source_id: str, db: Session = Depends(get_db)):
    row = source_service.get_source(db, source_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    node = db.get(RoadNode, row.node_id)
    return SupplySourceOut.from_model(row, node)
