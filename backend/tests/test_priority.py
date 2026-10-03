from datetime import datetime, timedelta

from app.algorithms.dto import EdgeDTO, InventoryLineDTO, NodeDTO, RequestDTO, SourceDTO
from app.algorithms.graph import RoadGraph
from app.algorithms.priority import PriorityWeights, compute_priorities

NOW = datetime(2026, 1, 1, 12, 0, 0)
NODES = [NodeDTO("A", "A", 0, 0), NodeDTO("B", "B", 0, 1)]
EDGES = [EdgeDTO("E1", "A", "B", 10.0, "OPEN")]
WEIGHTS = PriorityWeights(urgency=0.4, population_need=0.25, supply_deficit=0.25, accessibility=0.1)


def req(id_, urgency, required, people, area="B"):
    return RequestDTO(
        id=id_,
        area_id=area,
        area_name=area,
        resource="Food",
        required=required,
        unit="kg",
        people_affected=people,
        urgency=urgency,
        deadline=NOW + timedelta(hours=5),
        created_at=NOW,
    )


def source(available):
    return SourceDTO(
        id="S1", name="S1", node_id="A", verified=True, partner_org="org",
        inventory=[InventoryLineDTO(resource="Food", unit="kg", available=available)],
    )


def test_critical_urgency_scores_higher_than_low_all_else_equal():
    graph = RoadGraph(NODES, EDGES)
    requests = [req("R1", "Critical", 100, 500), req("R2", "Low", 100, 500)]
    priorities = compute_priorities(requests, [source(1000)], graph, WEIGHTS)
    assert priorities["R1"].priority_score > priorities["R2"].priority_score
    assert priorities["R1"].urgency_score == 1.0
    assert priorities["R2"].urgency_score == 0.25


def test_priority_sorting_orders_requests_descending():
    graph = RoadGraph(NODES, EDGES)
    requests = [req("LOW", "Low", 100, 100), req("CRIT", "Critical", 100, 5000), req("MED", "Medium", 100, 500)]
    priorities = compute_priorities(requests, [source(1000)], graph, WEIGHTS)
    ordered = sorted(requests, key=lambda r: priorities[r.id].priority_score, reverse=True)
    assert [r.id for r in ordered] == ["CRIT", "MED", "LOW"]


def test_supply_deficit_score_rises_as_available_inventory_shrinks():
    graph = RoadGraph(NODES, EDGES)
    requests = [req("R1", "Medium", 100, 500)]
    abundant = compute_priorities(requests, [source(10_000)], graph, WEIGHTS)["R1"]
    scarce = compute_priorities(requests, [source(10)], graph, WEIGHTS)["R1"]
    assert scarce.supply_deficit_score > abundant.supply_deficit_score


def test_accessibility_score_is_zero_when_no_route_exists():
    graph = RoadGraph(NODES, [])  # no edges at all -> nothing reachable
    requests = [req("R1", "Medium", 100, 500)]
    result = compute_priorities(requests, [source(1000)], graph, WEIGHTS)["R1"]
    assert result.accessibility_score == 0.0


def test_priority_breakdown_includes_explanation_text():
    graph = RoadGraph(NODES, EDGES)
    requests = [req("R1", "High", 100, 500)]
    result = compute_priorities(requests, [source(1000)], graph, WEIGHTS)["R1"]
    assert "High" in result.explanation
    assert isinstance(result.priority_score, float)
