from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.algorithms.priority import PriorityWeights
from app.config import settings
from app.models import AffectedRequest, Delivery, RoadEdge, SupplySource, Vehicle
from app.services import converters
from app.services.config_service import get_or_create_config, weights_from_config
from app.utils.time import now as time_now


@dataclass
class OperationalSummary:
    region: str
    system_status: str
    last_plan_generated_at: datetime | None
    critical_needs: int
    active_deliveries: int
    resource_coverage_pct: float
    vehicles_available: int
    at_risk_deliveries: int


@dataclass
class AlgorithmSnapshot:
    requests_evaluated: int
    verified_sources: int
    available_vehicles: int
    feasible_routes: int
    minimum_coverage_pct: float
    plan_generated_at: datetime | None
    priority_weights: PriorityWeights


@dataclass
class Coordinator:
    name: str
    role: str
    region: str
    initials: str


COORDINATOR = Coordinator(name="Aditi Desai", role="Relief Coordinator", region=settings.region_name, initials="AD")


def get_operational_summary(db: Session) -> OperationalSummary:
    requests = db.query(AffectedRequest).all()
    deliveries = db.query(Delivery).all()
    vehicles = db.query(Vehicle).all()
    config = get_or_create_config(db)

    total_required = sum(r.required for r in requests) or 1.0
    total_allocated = sum(r.allocated for r in requests)
    critical_needs = sum(1 for r in requests if r.urgency == "Critical" and r.status != "Fulfilled")
    active_deliveries = sum(1 for d in deliveries if d.status != "Delivered")
    vehicles_available = sum(1 for v in vehicles if v.status == "Available")

    at_risk = 0
    for d in deliveries:
        if d.status == "Delivered":
            continue
        if d.eta > d.deadline - timedelta(minutes=20):
            at_risk += 1

    blocked_roads = db.query(RoadEdge).filter(RoadEdge.condition == "BLOCKED").count()
    system_status = "Degraded" if (blocked_roads > 0 and critical_needs > 0) else "Operational"

    return OperationalSummary(
        region=settings.region_name,
        system_status=system_status,
        last_plan_generated_at=config.plan_generated_at,
        critical_needs=critical_needs,
        active_deliveries=active_deliveries,
        resource_coverage_pct=round((total_allocated / total_required) * 100, 1),
        vehicles_available=vehicles_available,
        at_risk_deliveries=at_risk,
    )


def get_algorithm_snapshot(db: Session) -> AlgorithmSnapshot:
    config = get_or_create_config(db)
    requests = db.query(AffectedRequest).all()
    sources = db.query(SupplySource).all()
    vehicles = db.query(Vehicle).all()

    verified_sources = sum(1 for s in sources if s.verified)
    available_vehicles = sum(1 for v in vehicles if v.status == "Available")

    graph = converters.build_graph(db)
    source_dtos = converters.load_sources(db)
    feasible_pairs = 0
    for req in requests:
        for src in source_dtos:
            if src.line_for(req.resource) is None:
                continue
            if graph.shortest_path(src.node_id, req.area_id) is not None:
                feasible_pairs += 1

    return AlgorithmSnapshot(
        requests_evaluated=len(requests),
        verified_sources=verified_sources,
        available_vehicles=available_vehicles,
        feasible_routes=feasible_pairs,
        minimum_coverage_pct=round(config.minimum_coverage_pct * 100, 0),
        plan_generated_at=config.plan_generated_at,
        priority_weights=weights_from_config(config),
    )


def get_coordinator() -> Coordinator:
    return COORDINATOR


def reset_demo(db: Session) -> None:
    """Wipe every table and reseed from scratch (section 4: 'POST
    /system/reset-demo'). Deterministic: the same allocation run against
    a freshly reset database produces the same plan, since the seed data
    and the algorithm are both deterministic — only `app.utils.time.now()`
    (real wall-clock) varies between reset runs, which only shifts
    absolute deadlines/ETAs, not which requests/sources/vehicles/routes
    get chosen.
    """
    from app.models import (
        AffectedRequest,
        Allocation,
        AlgorithmConfig,
        Delivery,
        DeliveryPartner,
        PlanSnapshot,
        ReplanEvent,
        RoadEdge,
        RoadNode,
        SourceInventory,
        SupplySource,
        TrackingEvent,
        Vehicle,
        VehicleCargo,
    )

    # Delete in FK-safe order (children before parents).
    for model in (
        TrackingEvent,
        Delivery,
        Allocation,
        ReplanEvent,
        PlanSnapshot,
        VehicleCargo,
        Vehicle,
        DeliveryPartner,
        SourceInventory,
        SupplySource,
        AffectedRequest,
        RoadEdge,
        RoadNode,
        AlgorithmConfig,
    ):
        db.query(model).delete()
    db.commit()

    from app.data.seed import seed_all

    seed_all(db)


def get_region_meta(db: Session) -> dict:
    nodes = converters.load_nodes(db)
    if not nodes:
        center = {"lat": 30.15, "lng": 79.1}
    else:
        center = {
            "lat": round(sum(n.lat for n in nodes) / len(nodes), 4),
            "lng": round(sum(n.lng for n in nodes) / len(nodes), 4),
        }
    return {"region": settings.region_name, "center": center, "zoom": 8}
