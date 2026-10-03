from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.common import CamelModel
from app.schemas.road import RoadEdgeOut, RoadNodeOut
from app.services import road_service

router = APIRouter(prefix="/roads", tags=["roads"])


class RoadsOut(CamelModel):
    nodes: list[RoadNodeOut]
    edges: list[RoadEdgeOut]


@router.get("", response_model=RoadsOut)
def get_roads(db: Session = Depends(get_db)):
    nodes = [RoadNodeOut.from_model(n) for n in road_service.list_nodes(db)]
    edges = [RoadEdgeOut.from_model(e) for e in road_service.list_edges(db)]
    return RoadsOut(nodes=nodes, edges=edges)
