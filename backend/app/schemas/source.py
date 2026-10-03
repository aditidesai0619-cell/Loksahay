from __future__ import annotations

from app.models import RoadNode, SupplySource
from app.schemas.common import CamelModel, LatLng


class InventoryLineOut(CamelModel):
    resource: str
    unit: str
    available: float
    allocated: float
    delivered: float


class SupplySourceOut(CamelModel):
    id: str
    name: str
    type: str
    location: LatLng
    verified: bool
    inventory: list[InventoryLineOut]
    partner_org: str

    @staticmethod
    def from_model(row: SupplySource, node: RoadNode) -> "SupplySourceOut":
        return SupplySourceOut(
            id=row.id,
            name=row.name,
            type=row.type,
            location=LatLng(lat=node.lat, lng=node.lng),
            verified=row.verified,
            inventory=[
                InventoryLineOut(
                    resource=line.resource, unit=line.unit, available=line.available, allocated=line.allocated, delivered=line.delivered
                )
                for line in row.inventory
            ],
            partnerOrg=row.partner_org,
        )
