from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AlgorithmConfig(Base):
    """Single-row table holding the configurable priority engine weights
    and fairness target. Section 11/12 require these to be configurable
    rather than hardcoded constants."""

    __tablename__ = "algorithm_config"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    urgency_weight: Mapped[float] = mapped_column(Float, nullable=False)
    population_need_weight: Mapped[float] = mapped_column(Float, nullable=False)
    supply_deficit_weight: Mapped[float] = mapped_column(Float, nullable=False)
    accessibility_weight: Mapped[float] = mapped_column(Float, nullable=False)
    minimum_coverage_pct: Mapped[float] = mapped_column(Float, nullable=False)
    plan_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PlanSnapshot(Base):
    """One row per allocation/replan/scenario-apply run — gives the
    Analytics screen a genuine (if short) history trend instead of
    fabricated numbers."""

    __tablename__ = "plan_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False, default="allocation.run")
    demand_fulfilled_pct: Mapped[float] = mapped_column(Float, nullable=False)
    critical_demand_fulfilled_pct: Mapped[float] = mapped_column(Float, nullable=False)
    on_time_delivery_pct: Mapped[float] = mapped_column(Float, nullable=False)
    total_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    vehicle_trips: Mapped[int] = mapped_column(Integer, nullable=False)
    unmet_demand_units: Mapped[float] = mapped_column(Float, nullable=False)
