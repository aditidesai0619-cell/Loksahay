from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ReplanEvent(Base):
    __tablename__ = "replan_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    trigger_description: Mapped[str] = mapped_column(String, nullable=False)
    # Road Blocked | Vehicle Unavailable | Inventory Shortfall | New Request
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)

    affected_delivery_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    vehicles_affected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deadlines_at_risk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    old_plan: Mapped[dict] = mapped_column(JSON, nullable=False)
    new_plan: Mapped[dict] = mapped_column(JSON, nullable=False)
    alternatives_considered: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    metrics_before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metrics_after: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Which allocation this replan would retarget, and to what, so /apply
    # can actually mutate it.
    target_allocation_id: Mapped[str | None] = mapped_column(String, nullable=True)
    new_source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    new_vehicle_id: Mapped[str | None] = mapped_column(String, nullable=True)
    new_route_node_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    new_route_edge_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    new_distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_eta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Pending | Applied | Dismissed
    status: Mapped[str] = mapped_column(String, nullable=False, default="Pending")
