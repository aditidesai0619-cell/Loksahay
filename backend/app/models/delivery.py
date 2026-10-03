from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    allocation_id: Mapped[str] = mapped_column(ForeignKey("allocations.id"), nullable=False, unique=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    request_id: Mapped[str] = mapped_column(ForeignKey("affected_requests.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("supply_sources.id"), nullable=False)

    route_node_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    route_edge_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)

    cargo: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    origin_name: Mapped[str] = mapped_column(String, nullable=False)
    destination_name: Mapped[str] = mapped_column(String, nullable=False)

    eta: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Assigned | Accepted | Picked Up | In Transit | Arrived | Delivered
    status: Mapped[str] = mapped_column(String, nullable=False, default="Assigned")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    events: Mapped[list["TrackingEvent"]] = relationship(
        back_populates="delivery", cascade="all, delete-orphan", order_by="TrackingEvent.timestamp"
    )

    @property
    def route_id(self) -> str:
        return f"RT-{self.allocation_id}"


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    delivery_id: Mapped[str] = mapped_column(ForeignKey("deliveries.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    delivery: Mapped[Delivery] = relationship(back_populates="events")
