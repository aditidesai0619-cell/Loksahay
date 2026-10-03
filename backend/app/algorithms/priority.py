"""Priority engine (section 11).

Priority = w_urgency * urgency_score
         + w_population * population_need_score
         + w_supply_deficit * supply_deficit_score
         + w_accessibility * accessibility_score

All four component scores are normalized to [0, 1] before weighting.
These weights and the mapping from raw inputs to [0, 1] scores are
PROTOTYPE ASSUMPTIONS for the APSH demonstration — not an official
disaster-response prioritization standard. Weights are configurable
(see `AlgorithmConfig` / GET+PUT /algorithm/config) rather than baked in.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.algorithms.dto import PriorityBreakdownDTO, RequestDTO, SourceDTO
from app.algorithms.graph import RoadGraph

URGENCY_SCORE = {"Critical": 1.0, "High": 0.75, "Medium": 0.5, "Low": 0.25}


@dataclass
class PriorityWeights:
    urgency: float
    population_need: float
    supply_deficit: float
    accessibility: float


def _normalize(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return max(0.0, min(1.0, value / max_value))


def compute_accessibility_scores(
    requests: list[RequestDTO],
    sources: list[SourceDTO],
    graph: RoadGraph,
) -> dict[str, float]:
    """For each request, find the fastest feasible travel time to any
    source that stocks a matching resource, then normalize those times
    across the batch (faster access -> higher score). A request with no
    feasible source at all scores 0.
    """
    best_time: dict[str, float] = {}
    for req in requests:
        candidates = [s for s in sources if s.line_for(req.resource) is not None]
        times: list[float] = []
        for src in candidates:
            route = graph.shortest_path(src.node_id, req.area_id)
            if route is not None:
                times.append(route.travel_time_min)
        best_time[req.id] = min(times) if times else -1.0

    reachable_times = [t for t in best_time.values() if t >= 0]
    max_time = max(reachable_times) if reachable_times else 1.0

    scores: dict[str, float] = {}
    for req in requests:
        t = best_time[req.id]
        if t < 0:
            scores[req.id] = 0.0
        else:
            # Closer (smaller travel time) -> higher accessibility.
            scores[req.id] = round(1.0 - _normalize(t, max_time), 4)
    return scores


def compute_priorities(
    requests: list[RequestDTO],
    sources: list[SourceDTO],
    graph: RoadGraph,
    weights: PriorityWeights,
) -> dict[str, PriorityBreakdownDTO]:
    if not requests:
        return {}

    max_population = max((r.people_affected for r in requests), default=1) or 1
    accessibility_scores = compute_accessibility_scores(requests, sources, graph)

    # Total network-wide inventory per resource, independent of any one
    # request, used for the supply-deficit score.
    total_available_by_resource: dict[str, float] = {}
    for src in sources:
        for line in src.inventory:
            total_available_by_resource[line.resource] = (
                total_available_by_resource.get(line.resource, 0.0) + line.available
            )

    result: dict[str, PriorityBreakdownDTO] = {}
    for req in requests:
        urgency_score = URGENCY_SCORE.get(req.urgency, 0.5)
        population_score = round(_normalize(req.people_affected, max_population), 4)

        total_available = total_available_by_resource.get(req.resource, 0.0)
        supply_deficit_score = round(
            max(0.0, min(1.0, (req.required - total_available) / req.required)) if req.required else 0.0,
            4,
        )
        accessibility_score = accessibility_scores[req.id]

        priority = (
            weights.urgency * urgency_score
            + weights.population_need * population_score
            + weights.supply_deficit * supply_deficit_score
            + weights.accessibility * accessibility_score
        )

        explanation = (
            f"{req.urgency} urgency ({urgency_score:.2f}), "
            f"population need {population_score:.2f} ({req.people_affected} affected vs. "
            f"{max_population} max in batch), supply deficit {supply_deficit_score:.2f} "
            f"({total_available:g} {req.unit} available network-wide vs. {req.required:g} required), "
            f"accessibility {accessibility_score:.2f}."
        )

        result[req.id] = PriorityBreakdownDTO(
            request_id=req.id,
            priority_score=round(priority, 4),
            urgency_score=urgency_score,
            population_need_score=population_score,
            supply_deficit_score=supply_deficit_score,
            accessibility_score=accessibility_score,
            explanation=explanation,
        )
    return result
