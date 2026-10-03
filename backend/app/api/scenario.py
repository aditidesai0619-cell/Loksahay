from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.common import CamelModel
from app.schemas.scenario import ScenarioActionIn, ScenarioResultOut
from app.services import scenario_service

router = APIRouter(prefix="/scenario", tags=["scenario"])


class ScenarioIn(CamelModel):
    actions: list[ScenarioActionIn]


def _to_engine_actions(actions: list[ScenarioActionIn]) -> list[dict]:
    return [a.model_dump(exclude={"id"}) for a in actions]


@router.post("/simulate", response_model=ScenarioResultOut)
def simulate_scenario(body: ScenarioIn, db: Session = Depends(get_db)):
    try:
        result = scenario_service.simulate_scenario(db, _to_engine_actions(body.actions))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ScenarioResultOut.from_result(result)


@router.post("/apply", response_model=ScenarioResultOut)
def apply_scenario(body: ScenarioIn, db: Session = Depends(get_db)):
    try:
        result = scenario_service.apply_scenario(db, _to_engine_actions(body.actions))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ScenarioResultOut.from_result(result)
