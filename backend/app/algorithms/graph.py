"""Road network as a weighted graph, routed with Dijkstra's algorithm.

Nodes = locations (towns/depots). Edges = road segments, weighted by
travel time in minutes (distance / condition-dependent speed). BLOCKED
edges are excluded from the graph entirely, so the routing algorithm can
never propose a blocked road — it simply does not exist as an edge to
traverse.

Complexity: building the adjacency list is O(N + E). Each `shortest_path`
call is O(E log N) using a binary-heap priority queue (standard Dijkstra).
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from app.algorithms.dto import EdgeDTO, NodeDTO
from app.config import settings


def edge_speed_kmh(condition: str) -> float:
    if condition == "DEGRADED":
        return settings.speed_kmh_degraded
    return settings.speed_kmh_clear


def edge_travel_time_min(edge: EdgeDTO) -> float:
    return edge.distance_km / edge_speed_kmh(edge.condition) * 60.0


@dataclass
class RouteResult:
    node_ids: list[str]
    edge_ids: list[str]
    distance_km: float
    travel_time_min: float
    feasible: bool


class RoadGraph:
    def __init__(self, nodes: list[NodeDTO], edges: list[EdgeDTO]):
        self.nodes: dict[str, NodeDTO] = {n.id: n for n in nodes}
        self.edges: list[EdgeDTO] = edges
        self._adjacency: dict[str, list[EdgeDTO]] = {n.id: [] for n in nodes}
        for edge in edges:
            if edge.condition == "BLOCKED":
                continue
            self._adjacency[edge.from_id].append(edge)
            # Roads are bidirectional.
            self._adjacency[edge.to_id].append(
                EdgeDTO(
                    id=edge.id,
                    from_id=edge.to_id,
                    to_id=edge.from_id,
                    distance_km=edge.distance_km,
                    condition=edge.condition,
                    blocked_reason=edge.blocked_reason,
                )
            )

    def shortest_path(self, source_node_id: str, target_node_id: str) -> RouteResult | None:
        """Dijkstra's algorithm, weighted by travel time (minutes)."""
        if source_node_id == target_node_id:
            return RouteResult([source_node_id], [], 0.0, 0.0, True)
        if source_node_id not in self._adjacency or target_node_id not in self._adjacency:
            return None

        dist: dict[str, float] = {source_node_id: 0.0}
        prev_node: dict[str, str] = {}
        prev_edge: dict[str, EdgeDTO] = {}
        visited: set[str] = set()
        heap: list[tuple[float, str]] = [(0.0, source_node_id)]

        while heap:
            d, node_id = heapq.heappop(heap)
            if node_id in visited:
                continue
            visited.add(node_id)
            if node_id == target_node_id:
                break
            for edge in self._adjacency.get(node_id, []):
                weight = edge_travel_time_min(edge)
                nd = d + weight
                if nd < dist.get(edge.to_id, float("inf")):
                    dist[edge.to_id] = nd
                    prev_node[edge.to_id] = node_id
                    prev_edge[edge.to_id] = edge
                    heapq.heappush(heap, (nd, edge.to_id))

        if target_node_id not in dist:
            return None

        node_path = [target_node_id]
        edge_path: list[str] = []
        cur = target_node_id
        while cur != source_node_id:
            edge_path.append(prev_edge[cur].id)
            cur = prev_node[cur]
            node_path.append(cur)
        node_path.reverse()
        edge_path.reverse()

        distance_km = self._sum_distance(edge_path)

        return RouteResult(
            node_ids=node_path,
            edge_ids=edge_path,
            distance_km=round(distance_km, 1),
            travel_time_min=round(dist[target_node_id], 1),
            feasible=True,
        )

    def _sum_distance(self, edge_ids: list[str]) -> float:
        by_id = {e.id: e for e in self.edges}
        return sum(by_id[eid].distance_km for eid in edge_ids)

    def path_latlng(self, node_ids: list[str]) -> list[dict]:
        return [{"lat": self.nodes[n].lat, "lng": self.nodes[n].lng} for n in node_ids if n in self.nodes]
