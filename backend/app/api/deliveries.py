from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.common import CamelModel
from app.schemas.delivery import DeliveryOut
from app.services import delivery_service

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


class DeliveryStatusIn(CamelModel):
    status: str
    note: str | None = None


@router.get("", response_model=list[DeliveryOut])
def list_deliveries(db: Session = Depends(get_db)):
    return [DeliveryOut.from_model(d) for d in delivery_service.list_deliveries(db)]


@router.get("/{delivery_id}", response_model=DeliveryOut)
def get_delivery(delivery_id: str, db: Session = Depends(get_db)):
    row = delivery_service.get_delivery(db, delivery_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Delivery {delivery_id} not found")
    return DeliveryOut.from_model(row)


@router.post("/{delivery_id}/status", response_model=DeliveryOut)
def advance_delivery_status(delivery_id: str, body: DeliveryStatusIn, db: Session = Depends(get_db)):
    try:
        row = delivery_service.advance_status(db, delivery_id, body.status, body.note)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DeliveryOut.from_model(row)
