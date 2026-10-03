from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import RoadNode
from app.schemas.common import CamelModel
from app.schemas.request import AffectedRequestOut
from app.schemas.road import RoadEdgeOut, RoadNodeOut
from app.schemas.source import SupplySourceOut
from app.schemas.system import RegionMetaOut
from app.schemas.vehicle import VehicleOut
from app.services import request_service, road_service, source_service, system_service, vehicle_service

router = APIRouter(tags=["map"])


class MapOut(CamelModel):
    region: RegionMetaOut
    nodes: list[RoadNodeOut]
    edges: list[RoadEdgeOut]
    requests: list[AffectedRequestOut]
    sources: list[SupplySourceOut]
    vehicles: list[VehicleOut]


@router.get("/map", response_model=MapOut)
def get_map(db: Session = Depends(get_db)):
    nodes_by_id = {n.id: n for n in db.query(RoadNode).all()}
    return MapOut(
        region=RegionMetaOut(**system_service.get_region_meta(db)),
        nodes=[RoadNodeOut.from_model(n) for n in road_service.list_nodes(db)],
        edges=[RoadEdgeOut.from_model(e) for e in road_service.list_edges(db)],
        requests=[AffectedRequestOut.from_model(r, nodes_by_id[r.area_id]) for r in request_service.list_requests(db)],
        sources=[SupplySourceOut.from_model(s, nodes_by_id[s.node_id]) for s in source_service.list_sources(db)],
        vehicles=[VehicleOut.from_model(v, nodes_by_id[v.node_id]) for v in vehicle_service.list_vehicles(db)],
    )
