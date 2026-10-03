from app.algorithms.dto import EdgeDTO, NodeDTO
from app.algorithms.graph import RoadGraph

NODES = [NodeDTO("A", "A", 0, 0), NodeDTO("B", "B", 0, 1), NodeDTO("C", "C", 0, 2), NodeDTO("D", "D", 0, 3)]


def make_graph(edges):
    return RoadGraph(NODES, edges)


def test_shortest_path_finds_direct_route():
    edges = [EdgeDTO("E1", "A", "B", 10.0, "OPEN")]
    graph = make_graph(edges)
    route = graph.shortest_path("A", "B")
    assert route is not None
    assert route.node_ids == ["A", "B"]
    assert route.edge_ids == ["E1"]
    assert route.feasible is True


def test_shortest_path_prefers_faster_route_over_shorter_distance():
    # A->B->D is 20km on OPEN roads (fast); A->C->D is 12km but DEGRADED
    # (slow) — Dijkstra here is weighted by travel TIME, so the longer
    # but faster route should win.
    edges = [
        EdgeDTO("E1", "A", "B", 10.0, "OPEN"),
        EdgeDTO("E2", "B", "D", 10.0, "OPEN"),
        EdgeDTO("E3", "A", "C", 6.0, "DEGRADED"),
        EdgeDTO("E4", "C", "D", 6.0, "DEGRADED"),
    ]
    graph = make_graph(edges)
    route = graph.shortest_path("A", "D")
    assert route is not None
    assert route.node_ids == ["A", "B", "D"]


def test_blocked_road_is_excluded_from_graph():
    edges = [
        EdgeDTO("E1", "A", "B", 10.0, "BLOCKED"),
        EdgeDTO("E2", "B", "C", 10.0, "OPEN"),
    ]
    graph = make_graph(edges)
    assert graph.shortest_path("A", "B") is None
    assert graph.shortest_path("B", "C") is not None


def test_no_path_returns_none_when_disconnected():
    edges = [EdgeDTO("E1", "A", "B", 10.0, "OPEN")]
    graph = make_graph(edges)
    assert graph.shortest_path("A", "D") is None


def test_roads_are_bidirectional():
    edges = [EdgeDTO("E1", "A", "B", 10.0, "OPEN")]
    graph = make_graph(edges)
    forward = graph.shortest_path("A", "B")
    backward = graph.shortest_path("B", "A")
    assert forward is not None and backward is not None
    assert forward.distance_km == backward.distance_km


def test_blocked_road_forces_a_longer_alternative_route():
    edges = [
        EdgeDTO("E1", "A", "B", 5.0, "BLOCKED"),
        EdgeDTO("E2", "A", "C", 5.0, "OPEN"),
        EdgeDTO("E3", "C", "B", 5.0, "OPEN"),
    ]
    graph = make_graph(edges)
    route = graph.shortest_path("A", "B")
    assert route is not None
    assert route.node_ids == ["A", "C", "B"]
