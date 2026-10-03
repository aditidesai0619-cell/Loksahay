from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class AffectedRequest(Base):
    __tablename__ = "affected_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    area_id: Mapped[str] = mapped_column(ForeignKey("road_nodes.id"), nullable=False)
    area_name: Mapped[str] = mapped_column(String, nullable=False)
    resource: Mapped[str] = mapped_column(String, nullable=False)  # Food | Medicine | Water | Essentials
    required: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    allocated: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    people_affected: Mapped[int] = mapped_column(Integer, nullable=False)
    urgency: Mapped[str] = mapped_column(String, nullable=False)  # Critical | High | Medium | Low
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="Unfulfilled")
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    alternative_source_name: Mapped[str | None] = mapped_column(String, nullable=True)
    alternative_eta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    area: Mapped["RoadNode"] = relationship()  # noqa: F821
