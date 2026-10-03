from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DeliveryPartner(Base):
    """A delivery-partner organization. Deliberately NOT foreign-keyed to
    Vehicle — `Vehicle.partner` (an existing, unchanged column) is matched
    to `DeliveryPartner.name` by the service layer, so this is purely
    additive: no existing table/column is modified."""

    __tablename__ = "delivery_partners"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    contact_person: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
