from __future__ import annotations

from app.models import Delivery
from app.schemas.common import CamelModel, LatLng
from app.utils.time import iso


class CargoLineOut(CamelModel):
    resource: str
    quantity: float
    unit: str


class TrackingEventOut(CamelModel):
    id: str
    status: str
    timestamp: str
    note: str | None = None
    location: LatLng | None = None

    @staticmethod
    def from_model(row) -> "TrackingEventOut":
        return TrackingEventOut(
            id=row.id,
            status=row.status,
            timestamp=iso(row.timestamp),
            note=row.note,
            location=LatLng(lat=row.lat, lng=row.lng) if row.lat is not None and row.lng is not None else None,
        )


class DeliveryOut(CamelModel):
    id: str
    allocation_id: str
    vehicle_id: str
    request_id: str
    source_id: str
    route_id: str
    cargo: list[CargoLineOut]
    origin_name: str
    destination_name: str
    distance_km: float
    eta_iso: str
    deadline_iso: str
    meets_deadline: bool
    status: str
    # Location of the most recent tracking event — i.e. the "current/last
    # known location" (section 2/4). Controlled/simulated (a waypoint along
    # the planned route keyed to lifecycle stage), not real GPS.
    current_location: LatLng | None = None
    events: list[TrackingEventOut]

    @staticmethod
    def from_model(row: Delivery) -> "DeliveryOut":
        last_event = row.events[-1] if row.events else None
        current_location = (
            LatLng(lat=last_event.lat, lng=last_event.lng)
            if last_event is not None and last_event.lat is not None and last_event.lng is not None
            else None
        )
        return DeliveryOut(
            id=row.id,
            allocationId=row.allocation_id,
            vehicleId=row.vehicle_id,
            requestId=row.request_id,
            sourceId=row.source_id,
            routeId=row.route_id,
            cargo=[CargoLineOut(resource=c["resource"], quantity=c["quantity"], unit=c["unit"]) for c in row.cargo],
            originName=row.origin_name,
            destinationName=row.destination_name,
            distanceKm=row.distance_km,
            etaIso=iso(row.eta),
            deadlineIso=iso(row.deadline),
            meetsDeadline=row.eta <= row.deadline,
            status=row.status,
            currentLocation=current_location,
            events=[TrackingEventOut.from_model(e) for e in row.events],
        )
