from datetime import datetime, timedelta

from app.algorithms.allocation_engine import run_allocation
from app.algorithms.baseline_engine import run_baseline_allocation
from app.algorithms.dto import EdgeDTO, InventoryLineDTO, NodeDTO, RequestDTO, SourceDTO, VehicleDTO, clone_requests, clone_sources, clone_vehicles
from app.algorithms.graph import RoadGraph
from app.algorithms.metrics import compute_metrics
from app.algorithms.priority import PriorityWeights

NOW = datetime(2026, 1, 1, 12, 0, 0)
WEIGHTS = PriorityWeights(urgency=0.4, population_need=0.25, supply_deficit=0.25, accessibility=0.1)

NODES = [
    NodeDTO("NEAR", "Near Source", 0, 0),
    NodeDTO("FAR", "Far Source", 0, 10),
    NodeDTO("AREA", "Affected Area", 0, 1),
]
EDGES = [
    EdgeDTO("E_NEAR", "NEAR", "AREA", 6.0, "OPEN"),
    EdgeDTO("E_FAR", "FAR", "AREA", 300.0, "DEGRADED"),  # much farther/slower
]


def base_requests():
    return [
        RequestDTO(
            id="REQ-OLD", area_id="AREA", area_name="Area", resource="Food", required=50, unit="kg",
            people_affected=200, urgency="Low", deadline=NOW + timedelta(hours=10), created_at=NOW - timedelta(hours=2),
        ),
        RequestDTO(
            id="REQ-NEW-CRITICAL", area_id="AREA", area_name="Area", resource="Food", required=50, unit="kg",
            people_affected=5000, urgency="Critical", deadline=NOW + timedelta(hours=10), created_at=NOW,
        ),
    ]


def base_sources():
    # The near source only has enough for ONE of the two requests.
    return [
        SourceDTO(id="NEAR_SRC", name="Near", node_id="NEAR", verified=True, partner_org="o",
                  inventory=[InventoryLineDTO(resource="Food", unit="kg", available=50)]),
        SourceDTO(id="FAR_SRC", name="Far", node_id="FAR", verified=True, partner_org="o",
                  inventory=[InventoryLineDTO(resource="Food", unit="kg", available=50)]),
    ]


def base_vehicles():
    return [
        VehicleDTO(id="V1", partner="p", type="Truck", capacity_kg=10_000, node_id="NEAR", status="Available"),
        VehicleDTO(id="V2", partner="p", type="Truck", capacity_kg=10_000, node_id="FAR", status="Available"),
    ]


def test_baseline_ignores_priority_and_uses_first_come_order():
    # LokSahay should prefer the Critical request for the scarce near
    # source regardless of arrival order; baseline (first-come) should
    # instead favor whichever request was created first.
    graph = RoadGraph(NODES, EDGES)

    ls_requests, ls_sources, ls_vehicles = base_requests(), base_sources(), base_vehicles()
    run_allocation(ls_requests, ls_sources, ls_vehicles, graph, WEIGHTS, 0.0, NOW)
    ls_by_id = {r.id: r.allocated for r in ls_requests}

    bl_requests, bl_sources, bl_vehicles = base_requests(), base_sources(), base_vehicles()
    run_baseline_allocation(bl_requests, bl_sources, bl_vehicles, graph, NOW)
    bl_by_id = {r.id: r.allocated for r in bl_requests}

    assert ls_by_id["REQ-NEW-CRITICAL"] >= ls_by_id["REQ-OLD"]
    assert bl_by_id["REQ-OLD"] >= bl_by_id["REQ-NEW-CRITICAL"]


def test_baseline_does_not_split_across_multiple_sources():
    graph = RoadGraph(NODES, EDGES)
    requests = [
        RequestDTO(
            id="REQ-1", area_id="AREA", area_name="Area", resource="Food", required=100, unit="kg",
            people_affected=100, urgency="Medium", deadline=NOW + timedelta(hours=10), created_at=NOW,
        )
    ]
    sources = base_sources()  # 50 + 50 = 100 total, but split across two sources
    vehicles = base_vehicles()
    results, unmet = run_baseline_allocation(requests, sources, vehicles, graph, NOW)
    assert len({r.source_id for r in results}) == 1, "baseline should only ever draw from its single nearest source"
    assert requests[0].allocated == 50  # only the nearest source's stock, not both
    assert unmet and unmet[0].unmet == 50


def test_same_dataset_comparison_uses_identical_inputs():
    """Both algorithms must be scored against the SAME starting snapshot
    (section 23) — cloning must not let one run see the other's state."""
    graph = RoadGraph(NODES, EDGES)
    original_requests, original_sources, original_vehicles = base_requests(), base_sources(), base_vehicles()

    ls_requests = clone_requests(original_requests)
    ls_sources = clone_sources(original_sources)
    ls_vehicles = clone_vehicles(original_vehicles)
    ls_results, _, _ = run_allocation(ls_requests, ls_sources, ls_vehicles, graph, WEIGHTS, 0.6, NOW)

    bl_requests = clone_requests(original_requests)
    bl_sources = clone_sources(original_sources)
    bl_vehicles = clone_vehicles(original_vehicles)
    bl_results, _ = run_baseline_allocation(bl_requests, bl_sources, bl_vehicles, graph, NOW)

    # The original snapshot must be untouched by either run.
    assert original_requests[0].allocated == 0
    assert original_sources[0].inventory[0].allocated == 0

    ls_metrics = compute_metrics(ls_requests, ls_results)
    bl_metrics = compute_metrics(bl_requests, bl_results)
    # LokSahay never commits to an allocation whose ETA misses the
    # deadline (it leaves it as unmet demand instead); the naive baseline
    # allocates regardless and simply records the delivery as late. So
    # the one guarantee that must hold on ANY same-dataset comparison is
    # on-time reliability, not raw fulfilled-%% (a baseline can inflate
    # fulfilled-% precisely by overcommitting to late deliveries).
    assert ls_metrics.on_time_delivery_pct >= bl_metrics.on_time_delivery_pct
