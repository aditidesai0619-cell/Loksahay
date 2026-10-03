from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.bottleneck import BottleneckOut
from app.services import bottleneck_service

router = APIRouter(tags=["bottlenecks"])


@router.get("/bottlenecks", response_model=list[BottleneckOut])
def get_bottlenecks(db: Session = Depends(get_db)):
    return [BottleneckOut.from_dto(b) for b in bottleneck_service.compute_bottlenecks(db)]
