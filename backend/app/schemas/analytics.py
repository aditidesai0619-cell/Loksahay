from __future__ import annotations

from app.schemas.common import CamelModel
from app.schemas.scenario import ScenarioMetricsOut
from app.services.analytics_service import AnalyticsResult


class AlgorithmComparisonOut(CamelModel):
    label: str
    metrics: ScenarioMetricsOut


class HistoryPointOut(CamelModel):
    timestamp: str
    demand_fulfilled_pct: float
    on_time_delivery_pct: float


class AnalyticsResultOut(CamelModel):
    current: ScenarioMetricsOut
    loksahay: AlgorithmComparisonOut
    baseline: AlgorithmComparisonOut
    history: list[HistoryPointOut]

    @staticmethod
    def from_result(result: AnalyticsResult) -> "AnalyticsResultOut":
        return AnalyticsResultOut(
            current=ScenarioMetricsOut.from_metrics(result.current),
            loksahay=AlgorithmComparisonOut(label=result.loksahay.label, metrics=ScenarioMetricsOut.from_metrics(result.loksahay.metrics)),
            baseline=AlgorithmComparisonOut(label=result.baseline.label, metrics=ScenarioMetricsOut.from_metrics(result.baseline.metrics)),
            history=[
                HistoryPointOut(timestamp=h.timestamp, demandFulfilledPct=h.demand_fulfilled_pct, onTimeDeliveryPct=h.on_time_delivery_pct)
                for h in result.history
            ],
        )
