from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.analytics import AnalyticsResultOut
from app.services import analytics_service

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResultOut)
def get_analytics(db: Session = Depends(get_db)):
    result = analytics_service.get_analytics(db)
    return AnalyticsResultOut.from_result(result)
