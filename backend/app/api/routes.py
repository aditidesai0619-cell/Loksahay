from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.algorithms.graph import edge_travel_time_min
from app.db import get_db
from app.models import Allocation, RoadEdge, RoadNode
from app.schemas.route import RouteOut

router = APIRouter(prefix="/routes", tags=["routes"])


def _build_route_out(alloc: Allocation, node_lookup: dict[str, tuple[float, float]], edges_by_id: dict[str, RoadEdge]) -> RouteOut:
    eta_minutes = sum(edge_travel_time_min(_edge_dto(edges_by_id[e])) for e in alloc.route_edge_ids if e in edges_by_id)
    feasible = all(edges_by_id[e].condition != "BLOCKED" for e in alloc.route_edge_ids if e in edges_by_id)
    return RouteOut.build(
        route_id=alloc.route_id,
        node_ids=alloc.route_node_ids,
        edge_ids=alloc.route_edge_ids,
        distance_km=alloc.distance_km,
        eta_minutes=round(eta_minutes, 1),
        feasible=feasible,
        node_lookup=node_lookup,
    )


def _edge_dto(edge: RoadEdge):
    from app.algorithms.dto import EdgeDTO

    return EdgeDTO(edge.id, edge.from_node_id, edge.to_node_id, edge.distance_km, edge.condition, edge.blocked_reason)


@router.get("", response_model=list[RouteOut])
def list_routes(db: Session = Depends(get_db)):
    nodes = {n.id: (n.lat, n.lng) for n in db.query(RoadNode).all()}
    edges_by_id = {e.id: e for e in db.query(RoadEdge).all()}
    allocations = db.query(Allocation).all()
    return [_build_route_out(a, nodes, edges_by_id) for a in allocations]


@router.get("/{route_id}", response_model=RouteOut)
def get_route(route_id: str, db: Session = Depends(get_db)):
    allocation_id = route_id.removeprefix("RT-")
    alloc = db.get(Allocation, allocation_id)
    if alloc is None:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
    nodes = {n.id: (n.lat, n.lng) for n in db.query(RoadNode).all()}
    edges_by_id = {e.id: e for e in db.query(RoadEdge).all()}
    return _build_route_out(alloc, nodes, edges_by_id)
