from datetime import datetime, timedelta

from app.algorithms.allocation_engine import run_allocation
from app.algorithms.dto import EdgeDTO, InventoryLineDTO, NodeDTO, RequestDTO, SourceDTO, VehicleDTO
from app.algorithms.graph import RoadGraph
from app.algorithms.priority import PriorityWeights

NOW = datetime(2026, 1, 1, 12, 0, 0)
WEIGHTS = PriorityWeights(urgency=0.4, population_need=0.25, supply_deficit=0.25, accessibility=0.1)

NODES = [
    NodeDTO("SRC_A", "Source A", 0, 0),
    NodeDTO("SRC_B", "Source B", 0, 1),
    NodeDTO("AREA", "Affected Area", 0, 2),
]
# Both sources are 10 minutes away from the affected area at 36 km/h (OPEN).
EDGES = [
    EdgeDTO("EA", "SRC_A", "AREA", 6.0, "OPEN"),
    EdgeDTO("EB", "SRC_B", "AREA", 6.0, "OPEN"),
]


def make_request(required=100, deadline_hours=5, urgency="High", resource="Food", unit="kg"):
    return RequestDTO(
        id="REQ-1",
        area_id="AREA",
        area_name="Affected Area",
        resource=resource,
        required=required,
        unit=unit,
        people_affected=1000,
        urgency=urgency,
        deadline=NOW + timedelta(hours=deadline_hours),
        created_at=NOW,
    )


def make_source(id_, node_id, available, resource="Food", unit="kg"):
    return SourceDTO(
        id=id_, name=id_, node_id=node_id, verified=True, partner_org="org",
        inventory=[InventoryLineDTO(resource=resource, unit=unit, available=available)],
    )


def make_vehicle(id_, capacity_kg=10_000, status="Available"):
    return VehicleDTO(id=id_, partner="partner", type="Truck", capacity_kg=capacity_kg, node_id="SRC_A", status=status)


def run(requests, sources, vehicles, min_coverage=0.6):
    graph = RoadGraph(NODES, EDGES)
    return run_allocation(requests, sources, vehicles, graph, WEIGHTS, min_coverage, NOW)


def test_full_allocation_when_resources_are_sufficient():
    requests = [make_request(required=100)]
    sources = [make_source("S1", "SRC_A", 500)]
    vehicles = [make_vehicle("V1")]
    results, unmet, _ = run(requests, sources, vehicles)
    assert unmet == []
    assert sum(r.quantity for r in results) == 100
    assert requests[0].allocated == 100


def test_allocation_never_exceeds_available_inventory():
    requests = [make_request(required=100)]
    sources = [make_source("S1", "SRC_A", 40)]  # only 40 available, need 100
    vehicles = [make_vehicle("V1")]
    results, unmet, _ = run(requests, sources, vehicles)
    assert sum(r.quantity for r in results) == 40
    assert sources[0].inventory[0].allocated == 40
    assert sources[0].inventory[0].remaining == 0
    assert unmet and unmet[0].unmet == 60


def test_allocation_never_exceeds_vehicle_capacity():
    # 1 kg per unit for Food; a 50kg-capacity vehicle can carry at most 50
    # units per trip. The engine allows a vehicle up to 2 trips/run, so
    # it should take two 50-unit trips rather than exceed capacity in one.
    requests = [make_request(required=100)]
    sources = [make_source("S1", "SRC_A", 500)]
    vehicles = [make_vehicle("V1", capacity_kg=50)]
    # min_coverage=1.0: this test is about per-trip capacity splitting in
    # isolation, not the fairness pass (which would otherwise spend both
    # of this vehicle's trips inside the capped pass-1 alone).
    results, unmet, _ = run(requests, sources, vehicles, min_coverage=1.0)
    assert all(r.quantity <= 50 for r in results)
    assert len(results) == 2
    assert requests[0].allocated == 100


def test_deadline_infeasible_allocation_is_rejected():
    # Source B is intentionally far (degraded, slow) so it cannot make a
    # 1-minute deadline; source A can.
    far_edges = [
        EdgeDTO("EA", "SRC_A", "AREA", 1.0, "OPEN"),
        EdgeDTO("EB", "SRC_B", "AREA", 500.0, "DEGRADED"),
    ]
    graph = RoadGraph(NODES, far_edges)
    requests = [make_request(required=50, deadline_hours=0.3)]  # 18 minutes
    sources = [make_source("S1", "SRC_B", 500)]  # only the far/slow source has stock
    vehicles = [make_vehicle("V1")]
    results, unmet, _ = run_allocation(requests, sources, vehicles, graph, WEIGHTS, 0.6, NOW)
    assert results == []
    assert unmet[0].reason == "Deadline infeasible"


def test_partial_allocation_when_inventory_runs_short():
    requests = [make_request(required=200)]
    sources = [make_source("S1", "SRC_A", 70)]
    vehicles = [make_vehicle("V1")]
    results, unmet, _ = run(requests, sources, vehicles)
    assert requests[0].allocated == 70
    assert unmet[0].required == 200
    assert unmet[0].allocated == 70
    assert unmet[0].unmet == 130


def test_request_can_be_split_across_multiple_sources():
    requests = [make_request(required=100)]
    sources = [make_source("S1", "SRC_A", 60), make_source("S2", "SRC_B", 50)]
    vehicles = [make_vehicle("V1"), make_vehicle("V2")]
    results, unmet, _ = run(requests, sources, vehicles)
    assert unmet == []
    assert requests[0].allocated == 100
    sources_used = {r.source_id for r in results}
    assert sources_used == {"S1", "S2"}
    # Exactly a 60/40 split (S1 fully drained, S2 tops up the remainder).
    by_source = {r.source_id: r.quantity for r in results}
    assert by_source["S1"] == 60
    assert by_source["S2"] == 40


def test_minimum_coverage_guarantees_low_priority_request_gets_something():
    # Scarce shared inventory: a Critical and a Low request both want it.
    # With minimum_coverage_pct=0.5, the Low request should still get at
    # least 50% of its ask reserved before the Critical request can take
    # everything in the uncapped top-up pass.
    low = make_request(required=100, urgency="Low")
    low.id = "REQ-LOW"
    critical = make_request(required=100, urgency="Critical")
    critical.id = "REQ-CRIT"
    sources = [make_source("S1", "SRC_A", 120)]
    vehicles = [make_vehicle("V1"), make_vehicle("V2"), make_vehicle("V3"), make_vehicle("V4")]
    results, unmet, _ = run([low, critical], sources, vehicles, min_coverage=0.5)
    assert low.allocated >= 50, "fairness pass should have reserved >= 50% of the Low request's ask"
    assert critical.allocated > low.allocated, "Critical should still outrank Low in the uncapped top-up pass"


def test_minimum_coverage_of_zero_lets_priority_dominate_completely():
    low = make_request(required=100, urgency="Low")
    low.id = "REQ-LOW"
    critical = make_request(required=100, urgency="Critical")
    critical.id = "REQ-CRIT"
    sources = [make_source("S1", "SRC_A", 100)]  # only enough for ONE request in full
    vehicles = [make_vehicle("V1"), make_vehicle("V2")]
    results, unmet, _ = run([low, critical], sources, vehicles, min_coverage=0.0)
    assert critical.allocated == 100
    assert low.allocated == 0


def test_unavailable_vehicle_is_never_assigned():
    requests = [make_request(required=50)]
    sources = [make_source("S1", "SRC_A", 500)]
    vehicles = [make_vehicle("V1", status="Unavailable")]
    results, unmet, _ = run(requests, sources, vehicles)
    assert results == []
    assert unmet[0].reason == "No feasible vehicle"


def test_source_with_no_matching_resource_is_never_considered():
    requests = [make_request(required=50, resource="Medicine", unit="kits")]
    sources = [make_source("S1", "SRC_A", 500, resource="Food", unit="kg")]
    vehicles = [make_vehicle("V1")]
    results, unmet, _ = run(requests, sources, vehicles)
    assert results == []
    assert unmet[0].reason == "Source unavailable"


def test_blocked_road_makes_a_request_unreachable():
    blocked_edges = [EdgeDTO("EA", "SRC_A", "AREA", 6.0, "BLOCKED"), EdgeDTO("EB", "SRC_B", "AREA", 6.0, "BLOCKED")]
    graph = RoadGraph(NODES, blocked_edges)
    requests = [make_request(required=50)]
    sources = [make_source("S1", "SRC_A", 500)]
    vehicles = [make_vehicle("V1")]
    results, unmet, _ = run_allocation(requests, sources, vehicles, graph, WEIGHTS, 0.6, NOW)
    assert results == []
    assert unmet[0].reason == "Road inaccessible"


def test_allocation_reasons_explain_the_selection():
    requests = [make_request(required=50)]
    sources = [make_source("S1", "SRC_A", 500)]
    vehicles = [make_vehicle("V1")]
    results, _, _ = run(requests, sources, vehicles)
    assert len(results[0].reasons) > 0
    assert any("priority score" in r for r in results[0].reasons)
