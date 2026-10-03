from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Vehicle


def list_vehicles(db: Session) -> list[Vehicle]:
    return db.query(Vehicle).order_by(Vehicle.id).all()


def get_vehicle(db: Session, vehicle_id: str) -> Vehicle | None:
    return db.get(Vehicle, vehicle_id)
