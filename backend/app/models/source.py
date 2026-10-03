from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SupplySource(Base):
    __tablename__ = "supply_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # Warehouse | Hospital | Relief Depot | Community Stock
    node_id: Mapped[str] = mapped_column(ForeignKey("road_nodes.id"), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    partner_org: Mapped[str] = mapped_column(String, nullable=False)

    node: Mapped["RoadNode"] = relationship()  # noqa: F821
    inventory: Mapped[list["SourceInventory"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class SourceInventory(Base):
    __tablename__ = "source_inventory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("supply_sources.id"), nullable=False)
    resource: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    available: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    allocated: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    delivered: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    source: Mapped[SupplySource] = relationship(back_populates="inventory")
