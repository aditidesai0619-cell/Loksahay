from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.partner import PartnerOut
from app.services import partner_service

router = APIRouter(prefix="/partners", tags=["partners"])


@router.get("", response_model=list[PartnerOut])
def list_partners(db: Session = Depends(get_db)):
    return [PartnerOut.from_summary(p) for p in partner_service.list_partners(db)]


@router.get("/{partner_id}", response_model=PartnerOut)
def get_partner(partner_id: str, db: Session = Depends(get_db)):
    summary = partner_service.get_partner(db, partner_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Partner {partner_id} not found")
    return PartnerOut.from_summary(summary)
