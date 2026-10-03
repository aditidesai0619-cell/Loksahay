from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Allocation
from app.schemas.allocation import AllocationOut
from app.schemas.common import CamelModel
from app.services import allocation_service

router = APIRouter(tags=["allocations"])


class ModifyAllocationIn(CamelModel):
    quantity: float


@router.get("/allocations", response_model=list[AllocationOut])
def list_allocations(db: Session = Depends(get_db)):
    rows = db.query(Allocation).order_by(Allocation.id).all()
    return [AllocationOut.from_model(r) for r in rows]


@router.get("/allocations/{allocation_id}", response_model=AllocationOut)
def get_allocation(allocation_id: str, db: Session = Depends(get_db)):
    row = db.get(Allocation, allocation_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Allocation {allocation_id} not found")
    return AllocationOut.from_model(row)


@router.post("/allocation/run", response_model=list[AllocationOut])
def run_allocation(db: Session = Depends(get_db)):
    """Re-plan open demand (section 13). Previously-committed
    (Accepted/Modified) allocations are untouched; everything still open
    is recomputed against current inventory/fleet/road conditions."""
    created = allocation_service.run_allocation_and_persist(db)
    return [AllocationOut.from_model(a) for a in created]


@router.post("/allocations/{allocation_id}/accept", response_model=AllocationOut)
def accept_allocation(allocation_id: str, db: Session = Depends(get_db)):
    try:
        alloc = allocation_service.accept_allocation(db, allocation_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AllocationOut.from_model(alloc)


@router.post("/allocations/{allocation_id}/reject", response_model=AllocationOut)
def reject_allocation(allocation_id: str, db: Session = Depends(get_db)):
    try:
        alloc = allocation_service.reject_allocation(db, allocation_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AllocationOut.from_model(alloc)


@router.post("/allocations/{allocation_id}/modify", response_model=AllocationOut)
def modify_allocation(allocation_id: str, body: ModifyAllocationIn, db: Session = Depends(get_db)):
    try:
        alloc = allocation_service.modify_allocation(db, allocation_id, body.quantity)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AllocationOut.from_model(alloc)
