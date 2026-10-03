from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.system import CoordinatorOut, OperationalSummaryOut, RegionMetaOut
from app.services import system_service

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/system/summary", response_model=OperationalSummaryOut)
def get_operational_summary(db: Session = Depends(get_db)):
    return OperationalSummaryOut.from_dto(system_service.get_operational_summary(db))


@router.get("/system/coordinator", response_model=CoordinatorOut)
def get_coordinator():
    return CoordinatorOut.from_dto(system_service.get_coordinator())


@router.get("/system/region", response_model=RegionMetaOut)
def get_region_meta(db: Session = Depends(get_db)):
    return RegionMetaOut(**system_service.get_region_meta(db))


@router.post("/system/reset-demo", response_model=OperationalSummaryOut)
def reset_demo(db: Session = Depends(get_db)):
    """Wipe and reseed the entire database back to the deterministic
    initial demo state — affected requests, sources, inventory, vehicles,
    roads, allocations, deliveries, tracking events, replan events, plan
    snapshots and algorithm config all return to their seed values."""
    system_service.reset_demo(db)
    return OperationalSummaryOut.from_dto(system_service.get_operational_summary(db))
