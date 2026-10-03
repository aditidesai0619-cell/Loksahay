from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    partner: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # Truck | Mini-Van | 4x4 | Motorbike
    capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    node_id: Mapped[str] = mapped_column(ForeignKey("road_nodes.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="Available")
    current_delivery_id: Mapped[str | None] = mapped_column(String, nullable=True)

    node: Mapped["RoadNode"] = relationship()  # noqa: F821
    cargo: Mapped[list["VehicleCargo"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )


class VehicleCargo(Base):
    """What a vehicle is currently carrying — cleared when it frees up."""

    __tablename__ = "vehicle_cargo"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    resource: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)

    vehicle: Mapped[Vehicle] = relationship(back_populates="cargo")
