from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import RoadEdge, RoadNode


def list_nodes(db: Session) -> list[RoadNode]:
    return db.query(RoadNode).order_by(RoadNode.id).all()


def list_edges(db: Session) -> list[RoadEdge]:
    return db.query(RoadEdge).order_by(RoadEdge.id).all()


def get_edge(db: Session, edge_id: str) -> RoadEdge | None:
    return db.get(RoadEdge, edge_id)


def set_edge_condition(db: Session, edge_id: str, condition: str, blocked_reason: str | None = None) -> RoadEdge:
    edge = get_edge(db, edge_id)
    if edge is None:
        raise LookupError(f"Road edge {edge_id} not found")
    edge.condition = condition
    edge.blocked_reason = blocked_reason if condition == "BLOCKED" else None
    db.commit()
    db.refresh(edge)
    return edge
