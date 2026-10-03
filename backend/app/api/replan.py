from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.common import CamelModel
from app.schemas.replan import ReplanEventOut
from app.services import replan_service

router = APIRouter(prefix="/replan", tags=["replan"])


class TriggerReplanIn(CamelModel):
    trigger_type: str
    target_id: str
    description: str
    value: float | None = None


@router.get("", response_model=list[ReplanEventOut])
def list_replans(db: Session = Depends(get_db)):
    return [ReplanEventOut.from_model(e) for e in replan_service.list_replans(db)]


@router.post("", response_model=ReplanEventOut)
def trigger_replan(body: TriggerReplanIn, db: Session = Depends(get_db)):
    try:
        event = replan_service.trigger_replan(db, body.trigger_type, body.target_id, body.description, body.value)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ReplanEventOut.from_model(event)


@router.post("/{replan_id}/apply", response_model=ReplanEventOut)
def apply_replan(replan_id: str, db: Session = Depends(get_db)):
    try:
        event = replan_service.apply_replan(db, replan_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ReplanEventOut.from_model(event)


@router.post("/{replan_id}/dismiss", response_model=ReplanEventOut)
def dismiss_replan(replan_id: str, db: Session = Depends(get_db)):
    try:
        event = replan_service.dismiss_replan(db, replan_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReplanEventOut.from_model(event)
