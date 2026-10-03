from __future__ import annotations

from app.schemas.common import CamelModel, LatLng


class RouteOut(CamelModel):
    id: str
    node_ids: list[str]
    edge_ids: list[str]
    distance_km: float
    eta_minutes: float
    path: list[LatLng]
    feasible: bool

    @staticmethod
    def build(
        route_id: str,
        node_ids: list[str],
        edge_ids: list[str],
        distance_km: float,
        eta_minutes: float,
        feasible: bool,
        node_lookup: dict[str, tuple[float, float]],
    ) -> "RouteOut":
        return RouteOut(
            id=route_id,
            nodeIds=node_ids,
            edgeIds=edge_ids,
            distanceKm=distance_km,
            etaMinutes=eta_minutes,
            path=[LatLng(lat=node_lookup[n][0], lng=node_lookup[n][1]) for n in node_ids if n in node_lookup],
            feasible=feasible,
        )
