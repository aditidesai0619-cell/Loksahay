from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import RoadNode
from app.schemas.vehicle import VehicleOut
from app.services import vehicle_service

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleOut])
def list_vehicles(db: Session = Depends(get_db)):
    rows = vehicle_service.list_vehicles(db)
    nodes = {n.id: n for n in db.query(RoadNode).all()}
    return [VehicleOut.from_model(r, nodes[r.node_id]) for r in rows]


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    row = vehicle_service.get_vehicle(db, vehicle_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    node = db.get(RoadNode, row.node_id)
    return VehicleOut.from_model(row, node)
