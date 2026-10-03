from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import RoadNode
from app.schemas.request import AffectedRequestOut
from app.services import request_service

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=list[AffectedRequestOut])
def list_requests(db: Session = Depends(get_db)):
    rows = request_service.list_requests(db)
    nodes = {n.id: n for n in db.query(RoadNode).all()}
    return [AffectedRequestOut.from_model(r, nodes[r.area_id]) for r in rows]


@router.get("/{request_id}", response_model=AffectedRequestOut)
def get_request(request_id: str, db: Session = Depends(get_db)):
    row = request_service.get_request(db, request_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    node = db.get(RoadNode, row.area_id)
    return AffectedRequestOut.from_model(row, node)
