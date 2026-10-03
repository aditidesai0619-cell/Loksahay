from __future__ import annotations

from app.schemas.common import CamelModel


class AlgorithmConfigIn(CamelModel):
    urgency_weight: float | None = None
    population_need_weight: float | None = None
    supply_deficit_weight: float | None = None
    accessibility_weight: float | None = None
    minimum_coverage_pct: float | None = None
