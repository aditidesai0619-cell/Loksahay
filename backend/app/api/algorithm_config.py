from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.config import AlgorithmConfigIn
from app.schemas.system import AlgorithmSnapshotOut
from app.services import config_service, system_service

router = APIRouter(prefix="/algorithm", tags=["algorithm"])


@router.get("/config", response_model=AlgorithmSnapshotOut)
def get_algorithm_config(db: Session = Depends(get_db)):
    return AlgorithmSnapshotOut.from_dto(system_service.get_algorithm_snapshot(db))


@router.put("/config", response_model=AlgorithmSnapshotOut)
def update_algorithm_config(body: AlgorithmConfigIn, db: Session = Depends(get_db)):
    # minimumCoveragePct is a 0-100 percent on the wire (matching what GET
    # returns), but stored internally as a 0-1 fraction — convert here, at
    # the one boundary between the public contract and internal storage.
    config_service.update_config(
        db,
        urgency_weight=body.urgency_weight,
        population_need_weight=body.population_need_weight,
        supply_deficit_weight=body.supply_deficit_weight,
        accessibility_weight=body.accessibility_weight,
        minimum_coverage_pct=(body.minimum_coverage_pct / 100 if body.minimum_coverage_pct is not None else None),
    )
    return AlgorithmSnapshotOut.from_dto(system_service.get_algorithm_snapshot(db))
