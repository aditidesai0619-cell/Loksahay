from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class RoadNode(Base):
    __tablename__ = "road_nodes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)


class RoadEdge(Base):
    __tablename__ = "road_edges"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    from_node_id: Mapped[str] = mapped_column(ForeignKey("road_nodes.id"), nullable=False)
    to_node_id: Mapped[str] = mapped_column(ForeignKey("road_nodes.id"), nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    # OPEN | DEGRADED | BLOCKED
    condition: Mapped[str] = mapped_column(String, nullable=False, default="OPEN")
    blocked_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    from_node: Mapped[RoadNode] = relationship(foreign_keys=[from_node_id])
    to_node: Mapped[RoadNode] = relationship(foreign_keys=[to_node_id])
