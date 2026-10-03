from __future__ import annotations

from sqlalchemy.orm import Session

from app.algorithms.priority import PriorityWeights
from app.config import settings
from app.models import AlgorithmConfig


def get_or_create_config(db: Session) -> AlgorithmConfig:
    config = db.get(AlgorithmConfig, 1)
    if config is None:
        config = AlgorithmConfig(
            id=1,
            urgency_weight=settings.default_priority_urgency,
            population_need_weight=settings.default_priority_population_need,
            supply_deficit_weight=settings.default_priority_supply_deficit,
            accessibility_weight=settings.default_priority_accessibility,
            minimum_coverage_pct=settings.default_minimum_coverage_pct,
            plan_generated_at=None,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def update_config(
    db: Session,
    *,
    urgency_weight: float | None = None,
    population_need_weight: float | None = None,
    supply_deficit_weight: float | None = None,
    accessibility_weight: float | None = None,
    minimum_coverage_pct: float | None = None,
) -> AlgorithmConfig:
    config = get_or_create_config(db)
    if urgency_weight is not None:
        config.urgency_weight = urgency_weight
    if population_need_weight is not None:
        config.population_need_weight = population_need_weight
    if supply_deficit_weight is not None:
        config.supply_deficit_weight = supply_deficit_weight
    if accessibility_weight is not None:
        config.accessibility_weight = accessibility_weight
    if minimum_coverage_pct is not None:
        config.minimum_coverage_pct = minimum_coverage_pct
    db.commit()
    db.refresh(config)
    return config


def weights_from_config(config: AlgorithmConfig) -> PriorityWeights:
    return PriorityWeights(
        urgency=config.urgency_weight,
        population_need=config.population_need_weight,
        supply_deficit=config.supply_deficit_weight,
        accessibility=config.accessibility_weight,
    )
