"""DB (SQLAlchemy ORM) <-> algorithm DTO conversion.

This is the only layer that should import both `app.models` and
`app.algorithms.dto` — it is the seam the allocation engine is isolated
behind, which is what lets `scenario_service` run the exact same engine
against a disposable in-memory clone.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.algorithms.dto import (
    AllocationResultDTO,
    EdgeDTO,
    InventoryLineDTO,
    NodeDTO,
    RequestDTO,
    SourceDTO,
    VehicleDTO,
)
from app.algorithms.graph import RoadGraph
from app.models import AffectedRequest, Allocation, RoadEdge, RoadNode, SourceInventory, SupplySource, Vehicle

COMMITTED_STATUSES = ("Accepted", "Modified")


def load_nodes(db: Session) -> list[NodeDTO]:
    return [NodeDTO(n.id, n.name, n.lat, n.lng) for n in db.query(RoadNode).all()]


def load_edges(db: Session) -> list[EdgeDTO]:
    return [
        EdgeDTO(e.id, e.from_node_id, e.to_node_id, e.distance_km, e.condition, e.blocked_reason)
        for e in db.query(RoadEdge).all()
    ]


def build_graph(db: Session) -> RoadGraph:
    return RoadGraph(load_nodes(db), load_edges(db))


def load_requests(db: Session, *, reset_allocated: bool = False) -> list[RequestDTO]:
    rows = db.query(AffectedRequest).all()
    return [
        RequestDTO(
            id=r.id,
            area_id=r.area_id,
            area_name=r.area_name,
            resource=r.resource,
            required=r.required,
            unit=r.unit,
            people_affected=r.people_affected,
            urgency=r.urgency,
            deadline=r.deadline,
            created_at=r.created_at,
            allocated=0.0 if reset_allocated else r.allocated,
        )
        for r in rows
    ]


def load_sources(db: Session, *, reset_allocated: bool = False) -> list[SourceDTO]:
    rows = db.query(SupplySource).all()
    sources = []
    for s in rows:
        sources.append(
            SourceDTO(
                id=s.id,
                name=s.name,
                node_id=s.node_id,
                verified=s.verified,
                partner_org=s.partner_org,
                inventory=[
                    InventoryLineDTO(
                        resource=line.resource,
                        unit=line.unit,
                        available=line.available,
                        allocated=0.0 if reset_allocated else line.allocated,
                    )
                    for line in s.inventory
                ],
            )
        )
    return sources


def load_vehicles(db: Session, *, reset_assignments: bool = False) -> list[VehicleDTO]:
    rows = db.query(Vehicle).all()
    vehicles = []
    for v in rows:
        if reset_assignments:
            status = "Unavailable" if v.status == "Unavailable" else "Available"
        else:
            status = v.status
        vehicles.append(
            VehicleDTO(
                id=v.id,
                partner=v.partner,
                type=v.type,
                capacity_kg=v.capacity_kg,
                node_id=v.node_id,
                status=status,
            )
        )
    return vehicles


def load_committed_snapshot(
    db: Session,
) -> tuple[list[RequestDTO], list[SourceDTO], list[VehicleDTO], list[Allocation]]:
    """Like load_requests/load_sources/load_vehicles, but 'allocated'
    reflects ONLY Accepted/Modified allocations — Proposed ones (not yet
    a coordinator decision) are excluded so they're treated as open
    demand again. Used by scenario simulation and replanning, which
    reconsider everything that isn't a firm commitment.

    Also returns the committed Allocation rows themselves, since callers
    need them to build a comparable "before" AllocationResultDTO list.
    """
    committed = db.query(Allocation).filter(Allocation.status.in_(COMMITTED_STATUSES)).all()

    requests = load_requests(db, reset_allocated=True)
    sources = load_sources(db, reset_allocated=True)
    vehicles = load_vehicles(db, reset_assignments=True)

    req_by_id = {r.id: r for r in requests}
    src_by_id = {s.id: s for s in sources}
    veh_by_id = {v.id: v for v in vehicles}

    for alloc in committed:
        req = req_by_id.get(alloc.request_id)
        if req is not None:
            req.allocated += alloc.quantity
        src = src_by_id.get(alloc.source_id)
        if src is not None:
            line = src.line_for(alloc.resource)
            if line is not None:
                line.allocated += alloc.quantity
        veh = veh_by_id.get(alloc.vehicle_id)
        if veh is not None:
            veh.trips += 1
            if veh.status != "Unavailable":
                veh.status = "Assigned"

    return requests, sources, vehicles, committed


def allocation_to_result_dto(alloc: Allocation, source_name: str, source_verified: bool) -> AllocationResultDTO:
    return AllocationResultDTO(
        request_id=alloc.request_id,
        source_id=alloc.source_id,
        source_name=source_name,
        source_verified=source_verified,
        vehicle_id=alloc.vehicle_id,
        resource=alloc.resource,
        quantity=alloc.quantity,
        unit=alloc.unit,
        route_node_ids=alloc.route_node_ids,
        route_edge_ids=alloc.route_edge_ids,
        distance_km=alloc.distance_km,
        eta_minutes=0.0,
        eta=alloc.eta,
        deadline=alloc.deadline,
        meets_deadline=alloc.meets_deadline,
        priority_score=alloc.priority_score,
        reasons=alloc.reasons,
    )
