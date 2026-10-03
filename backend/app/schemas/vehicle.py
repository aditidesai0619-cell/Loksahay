from __future__ import annotations

from app.algorithms.dto import cargo_weight_kg
from app.models import RoadNode, Vehicle
from app.schemas.common import CamelModel, LatLng


class CargoLineOut(CamelModel):
    resource: str
    quantity: float
    unit: str


class VehicleOut(CamelModel):
    id: str
    partner: str
    type: str
    capacity_kg: float
    cargo: list[CargoLineOut]
    # Real weight of current cargo in kg (section: VehicleCard load % must
    # not assume 1kg/unit for every resource — Medicine/Essentials/Food/
    # Water all convert differently; see `cargo_weight_kg`).
    cargo_weight_kg: float
    location: LatLng
    status: str
    current_delivery_id: str | None = None

    @staticmethod
    def from_model(row: Vehicle, node: RoadNode) -> "VehicleOut":
        total_weight = sum(cargo_weight_kg(c.resource, c.quantity) for c in row.cargo)
        return VehicleOut(
            id=row.id,
            partner=row.partner,
            type=row.type,
            capacityKg=row.capacity_kg,
            cargo=[CargoLineOut(resource=c.resource, quantity=c.quantity, unit=c.unit) for c in row.cargo],
            cargoWeightKg=round(total_weight, 2),
            location=LatLng(lat=node.lat, lng=node.lng),
            status=row.status,
            currentDeliveryId=row.current_delivery_id,
        )
