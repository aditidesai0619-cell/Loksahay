from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Allocation(Base):
    __tablename__ = "allocations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("affected_requests.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("supply_sources.id"), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"), nullable=False)

    route_node_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    route_edge_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)

    resource: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)

    eta: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    meets_deadline: Mapped[bool] = mapped_column(Boolean, nullable=False)

    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    # {urgencyScore, populationNeedScore, supplyDeficitScore, accessibilityScore}
    priority_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Proposed | Accepted | Modified | Rejected
    status: Mapped[str] = mapped_column(String, nullable=False, default="Proposed")
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    @property
    def route_id(self) -> str:
        return f"RT-{self.id}"
