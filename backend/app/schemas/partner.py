from __future__ import annotations

from app.schemas.common import CamelModel
from app.services.partner_service import PartnerSummary


class PartnerVehicleOut(CamelModel):
    vehicle_id: str
    type: str
    capacity_kg: float
    status: str
    current_delivery_id: str | None = None


class PartnerOut(CamelModel):
    id: str
    name: str
    contact_person: str
    phone: str
    vehicles: list[PartnerVehicleOut]
    completed_deliveries: int
    active_deliveries: int

    @staticmethod
    def from_summary(s: PartnerSummary) -> "PartnerOut":
        return PartnerOut(
            id=s.id,
            name=s.name,
            contactPerson=s.contact_person,
            phone=s.phone,
            vehicles=[
                PartnerVehicleOut(
                    vehicleId=v.vehicle_id,
                    type=v.type,
                    capacityKg=v.capacity_kg,
                    status=v.status,
                    currentDeliveryId=v.current_delivery_id,
                )
                for v in s.vehicles
            ],
            completedDeliveries=s.completed_deliveries,
            activeDeliveries=s.active_deliveries,
        )
