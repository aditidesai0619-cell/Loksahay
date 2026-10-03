"""Deterministic demo seed data (section 26).

Populates the Uttarakhand demo region with 10 affected areas, 7 supply
sources, 8 vehicles and 26 road edges (2 pre-blocked/degraded), then runs
the REAL allocation engine (not hardcoded allocations) to produce the
initial plan — so every allocation/delivery in the fresh database is a
genuine output of the algorithm, not scripted data.

It then walks through a short, realistic sequence of coordinator actions
(accepting most proposals, advancing a couple of deliveries, leaving one
proposal pending) and triggers one dynamic replan against whichever
committed delivery the algorithm happened to route through a segment we
then block — so the Replanning Center has a genuine, non-scripted
disruption to demonstrate.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.data.geo_seed import EDGES, NODES
from app.models import AffectedRequest, DeliveryPartner, RoadEdge, RoadNode, SourceInventory, SupplySource, Vehicle
from app.services import allocation_service, converters, delivery_service, replan_service
from app.services.config_service import get_or_create_config
from app.utils.time import minutes_from_now, now as time_now

REQUESTS = [
    # id, area_id, area_name, resource, required, unit, people_affected, urgency, deadline_min
    #
    # Deadlines are set relative to each area's REAL best-case travel time
    # over the seeded road graph (see the diagnostic used while tuning
    # this file), not arbitrary round numbers — otherwise every remote,
    # multi-hour-by-road area would trivially fail on deadline regardless
    # of which source/vehicle the algorithm picks. REQ-10 (Munsiyari) is
    # deliberately left unreachable-by-ground-in-time on purpose, as the
    # demo's dedicated "Deadline Constraint" bottleneck.
    ("REQ-01", "N-KED", "Kedarnath", "Medicine", 150, "kits", 1200, "Critical", 480),
    ("REQ-02", "N-GRK", "Gaurikund", "Food", 800, "kg", 950, "High", 300),
    ("REQ-03", "N-JOS", "Joshimath", "Water", 5000, "L", 3400, "Critical", 360),
    ("REQ-04", "N-RUD", "Rudraprayag", "Essentials", 300, "kits", 600, "Medium", 180),
    ("REQ-05", "N-UTK", "Uttarkashi", "Food", 1200, "kg", 2100, "High", 240),
    ("REQ-06", "N-GOP", "Gopeshwar (Chamoli)", "Medicine", 90, "kits", 1800, "High", 360),
    ("REQ-07", "N-KRN", "Karnaprayag", "Water", 2500, "L", 500, "Medium", 240),
    ("REQ-08", "N-BAG", "Bageshwar", "Essentials", 150, "kits", 300, "Low", 600),
    ("REQ-09", "N-PTG", "Pithoragarh", "Food", 900, "kg", 1100, "Medium", 600),
    ("REQ-10", "N-MUN", "Munsiyari", "Medicine", 60, "kits", 700, "Critical", 120),
]

SOURCES = [
    # id, name, type, node_id, verified, partner_org, [(resource, unit, available)]
    (
        "SRC-01", "Dehradun Central Warehouse", "Warehouse", "N-DDN", True, "State Disaster Response Force Depot",
        [("Food", "kg", 5000), ("Essentials", "kits", 2000), ("Water", "L", 8000)],
    ),
    (
        "SRC-02", "Haridwar Relief Depot", "Relief Depot", "N-HDR", True, "Red Cross Haridwar Chapter",
        [("Medicine", "kits", 400), ("Water", "L", 4000), ("Essentials", "kits", 1200)],
    ),
    (
        "SRC-03", "Rishikesh Hospital Stock", "Hospital", "N-RSK", True, "AIIMS Rishikesh",
        [("Medicine", "kits", 220)],
    ),
    (
        "SRC-04", "Srinagar Garhwal Warehouse", "Warehouse", "N-SRI", True, "Garhwal Civil Supplies",
        [("Food", "kg", 2200), ("Essentials", "kits", 800)],
    ),
    (
        "SRC-05", "Pauri Relief Depot", "Relief Depot", "N-PAU", True, "Uttarakhand SDRF",
        [("Water", "L", 3000), ("Food", "kg", 900)],
    ),
    (
        "SRC-06", "Kotdwar Community Stock", "Community Stock", "N-KDW", False, "Kotdwar Civil Society Collective",
        [("Essentials", "kits", 600), ("Food", "kg", 400)],
    ),
    (
        "SRC-07", "Almora Hospital", "Hospital", "N-ALM", True, "Base Hospital Almora",
        [("Medicine", "kits", 150), ("Food", "kg", 1400)],
    ),
]

VEHICLES = [
    # id, partner, type, capacity_kg, home_node_id
    ("V-01", "SDRF Fleet", "Truck", 3000, "N-RSK"),
    ("V-02", "Red Cross Logistics", "Truck", 4000, "N-SRI"),
    ("V-03", "SDRF Fleet", "4x4", 800, "N-HDR"),
    ("V-04", "Civil Supplies Dept.", "Mini-Van", 1200, "N-KDW"),
    ("V-05", "SDRF Fleet", "Truck", 3500, "N-SRI"),
    ("V-06", "Garhwal Civil Supplies", "4x4", 700, "N-ALM"),
    ("V-07", "Local Volunteer Corps", "Motorbike", 60, "N-BAG"),
    ("V-08", "Red Cross Logistics", "Truck", 2500, "N-PAU"),
]

# This one vehicle starts broken down so the Transport fleet summary shows
# every status category (Available/Assigned/In Transit/Delivered/Unavailable).
UNAVAILABLE_VEHICLE_ID = "V-07"

# One row per distinct Vehicle.partner string above — matched by name, not
# a foreign key, so the existing `vehicles` table is untouched. Contact
# details are demo data in the same spirit as the existing seed (e.g. the
# coordinator "Aditi Desai"), not a claim of real directory data.
PARTNERS = [
    # id, name (must match VEHICLES partner strings exactly), contact_person, phone
    ("PTR-01", "SDRF Fleet", "Inspector Rakesh Bisht", "+91 98765 10001"),
    ("PTR-02", "Red Cross Logistics", "Priya Nair", "+91 98765 10002"),
    ("PTR-03", "Civil Supplies Dept.", "Manoj Thapliyal", "+91 98765 10003"),
    ("PTR-04", "Garhwal Civil Supplies", "Sunita Rawat", "+91 98765 10004"),
    ("PTR-05", "Local Volunteer Corps", "Arjun Negi", "+91 98765 10005"),
]


def seed_all(db: Session) -> None:
    now = time_now()

    for node_id, name, lat, lng in NODES:
        db.add(RoadNode(id=node_id, name=name, lat=lat, lng=lng))
    db.flush()

    for edge_id, from_id, to_id, condition, reason in EDGES:
        db.add(RoadEdge(id=edge_id, from_node_id=from_id, to_node_id=to_id, distance_km=_haversine(from_id, to_id), condition=condition, blocked_reason=reason))
    db.flush()

    for req_id, area_id, area_name, resource, required, unit, people, urgency, deadline_min in REQUESTS:
        db.add(
            AffectedRequest(
                id=req_id,
                area_id=area_id,
                area_name=area_name,
                resource=resource,
                required=float(required),
                unit=unit,
                allocated=0.0,
                people_affected=people,
                urgency=urgency,
                deadline=minutes_from_now(deadline_min, now),
                status="Unfulfilled",
                created_at=minutes_from_now(-abs(deadline_min) / 2, now),
            )
        )

    for src_id, name, type_, node_id, verified, partner_org, inventory in SOURCES:
        db.add(SupplySource(id=src_id, name=name, type=type_, node_id=node_id, verified=verified, partner_org=partner_org))
        db.flush()
        for resource, unit, available in inventory:
            db.add(SourceInventory(source_id=src_id, resource=resource, unit=unit, available=float(available), allocated=0.0, delivered=0.0))

    for veh_id, partner, type_, capacity, home_node in VEHICLES:
        status = "Unavailable" if veh_id == UNAVAILABLE_VEHICLE_ID else "Available"
        db.add(Vehicle(id=veh_id, partner=partner, type=type_, capacity_kg=float(capacity), node_id=home_node, status=status))

    for partner_id, name, contact_person, phone in PARTNERS:
        db.add(DeliveryPartner(id=partner_id, name=name, contact_person=contact_person, phone=phone))

    get_or_create_config(db)
    db.commit()

    # Real engine run #1 — the initial plan. Snapshot #1.
    allocation_service.run_allocation_and_persist(db, snapshot_label="seed.initial_plan")

    _accept_most_proposals(db)
    # Snapshot #2 — after the coordinator reviews most proposals.
    from app.services.plan_snapshot_service import record_snapshot

    record_snapshot(db, label="seed.proposals_accepted")

    _advance_some_deliveries(db)
    # Snapshot #3 — after a couple of deliveries progress.
    record_snapshot(db, label="seed.deliveries_in_progress")

    _trigger_demo_replan(db)


def _accept_most_proposals(db: Session) -> None:
    from app.models import Allocation

    proposed = db.query(Allocation).filter(Allocation.status == "Proposed").order_by(Allocation.id).all()
    # Leave the last proposal pending so the Allocation Workspace has a
    # live decision to demonstrate.
    for alloc in proposed[:-1] if len(proposed) > 1 else proposed:
        allocation_service.accept_allocation(db, alloc.id)


def _advance_some_deliveries(db: Session) -> None:
    from app.models import Delivery

    deliveries = db.query(Delivery).order_by(Delivery.id).all()
    if not deliveries:
        return
    # First delivery: push through to Delivered.
    for stage in ["Accepted", "Picked Up", "In Transit", "Arrived", "Delivered"]:
        try:
            delivery_service.advance_status(db, deliveries[0].id, stage)
        except ValueError:
            break
    # Second delivery (if any): leave mid-transit.
    if len(deliveries) > 1:
        for stage in ["Accepted", "Picked Up", "In Transit"]:
            try:
                delivery_service.advance_status(db, deliveries[1].id, stage)
            except ValueError:
                break
    # Third delivery (if any): just accepted, not yet picked up.
    if len(deliveries) > 2:
        try:
            delivery_service.advance_status(db, deliveries[2].id, "Accepted")
        except ValueError:
            pass


def _probe_reroute_feasible(db: Session, alloc, edge_id: str) -> bool:
    """Dry-run only (no persistence): would SOME alternative still exist
    for this allocation's request if `edge_id` were blocked? Used to pick
    a demo disruption that actually has a feasible reroute, rather than
    one that strands the delivery outright."""
    from dataclasses import replace

    from app.algorithms.allocation_engine import run_allocation
    from app.algorithms.graph import RoadGraph
    from app.services.config_service import get_or_create_config, weights_from_config

    config = get_or_create_config(db)
    weights = weights_from_config(config)

    nodes = converters.load_nodes(db)
    edges = converters.load_edges(db)
    for e in edges:
        if e.id == edge_id:
            e.condition = "BLOCKED"
    graph = RoadGraph(nodes, edges)

    requests, sources, vehicles, _ = converters.load_committed_snapshot(db)
    req_dto = next(r for r in requests if r.id == alloc.request_id)
    req_dto.allocated = max(0.0, req_dto.allocated - alloc.quantity)
    src_dto = next(s for s in sources if s.id == alloc.source_id)
    line = src_dto.line_for(alloc.resource)
    if line:
        line.allocated = max(0.0, line.allocated - alloc.quantity)
    veh_dto = next(v for v in vehicles if v.id == alloc.vehicle_id)
    if veh_dto.status != "Unavailable":
        veh_dto.trips = max(0, veh_dto.trips - 1)
        veh_dto.status = "Available"

    single = replace(req_dto, required=alloc.quantity, allocated=0.0)
    results, _, _ = run_allocation([single], sources, vehicles, graph, weights, 1.0, time_now())
    return len(results) > 0


def _trigger_demo_replan(db: Session) -> None:
    from app.models import Allocation, Delivery

    committed = (
        db.query(Allocation)
        .filter(Allocation.status.in_(("Accepted", "Modified")))
        .join(Delivery, Delivery.allocation_id == Allocation.id)
        .filter(Delivery.status != "Delivered")
        .order_by(Allocation.id)
        .all()
    )
    if not committed:
        return

    # Try R7 first (narrative continuity with the frontend's original
    # demo: Tehri<->Srinagar, which has a good alternative via Pauri).
    # Otherwise probe every (allocation, edge) pair actually in use and
    # pick the first one that still has a feasible reroute, so the seed
    # reliably demonstrates a SUCCESSFUL replan rather than a dead end.
    candidates: list[tuple[object, str]] = []
    for a in committed:
        if "R7" in a.route_edge_ids:
            candidates.append((a, "R7"))
    for a in committed:
        for edge_id in a.route_edge_ids:
            candidates.append((a, edge_id))

    chosen = None
    for alloc, edge_id in candidates:
        if _probe_reroute_feasible(db, alloc, edge_id):
            chosen = (alloc, edge_id)
            break

    if chosen is None:
        # Nothing has a feasible alternative — still demonstrate the
        # feature with the first candidate (shows the "no feasible
        # reroute" path, which is itself a valid, honest outcome).
        chosen = candidates[0]

    _, target_edge = chosen
    try:
        replan_service.trigger_replan(
            db,
            trigger_type="Road Blocked",
            target_id=target_edge,
            description=f"Road {target_edge} blocked — landslide debris reported on the network.",
        )
    except ValueError:
        pass


def _haversine(from_id: str, to_id: str) -> float:
    import math

    nodes = {n[0]: (n[2], n[3]) for n in NODES}
    (lat1, lng1), (lat2, lng2) = nodes[from_id], nodes[to_id]
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    h = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    return round(r * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h)) * 1.35, 1)
