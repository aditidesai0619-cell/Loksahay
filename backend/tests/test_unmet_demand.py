from datetime import datetime, timedelta

from app.algorithms.allocation_engine import run_allocation
from app.algorithms.dto import EdgeDTO, InventoryLineDTO, NodeDTO, RequestDTO, SourceDTO, VehicleDTO
from app.algorithms.graph import RoadGraph
from app.algorithms.priority import PriorityWeights

NOW = datetime(2026, 1, 1, 12, 0, 0)
WEIGHTS = PriorityWeights(urgency=0.4, population_need=0.25, supply_deficit=0.25, accessibility=0.1)

NODES = [NodeDTO("SRC", "Source", 0, 0), NodeDTO("AREA", "Area", 0, 1)]
EDGES = [EdgeDTO("E1", "SRC", "AREA", 6.0, "OPEN")]


def test_unmet_demand_reports_required_allocated_and_unmet():
    graph = RoadGraph(NODES, EDGES)
    req = RequestDTO(
        id="REQ-1", area_id="AREA", area_name="Area", resource="Food", required=100, unit="kg",
        people_affected=100, urgency="Medium", deadline=NOW + timedelta(hours=5), created_at=NOW,
    )
    source = SourceDTO(
        id="S1", name="S1", node_id="SRC", verified=True, partner_org="o",
        inventory=[InventoryLineDTO(resource="Food", unit="kg", available=30)],
    )
    vehicle = VehicleDTO(id="V1", partner="p", type="Truck", capacity_kg=10_000, node_id="SRC", status="Available")

    _, unmet, _ = run_allocation([req], [source], [vehicle], graph, WEIGHTS, 0.6, NOW)

    assert len(unmet) == 1
    assert unmet[0].required == 100
    assert unmet[0].allocated == 30
    assert unmet[0].unmet == 70
    assert unmet[0].reason in {"Insufficient inventory", "No feasible vehicle"}


def test_unmet_demand_suggests_an_alternative_source_even_if_infeasible():
    # The source exists and has stock, but the vehicle cannot carry
    # enough and there's no second vehicle — still, the engine should
    # name the source and an ETA as the best-known alternative.
    graph = RoadGraph(NODES, EDGES)
    req = RequestDTO(
        id="REQ-1", area_id="AREA", area_name="Area", resource="Food", required=100, unit="kg",
        people_affected=100, urgency="Medium", deadline=NOW + timedelta(hours=5), created_at=NOW,
    )
    source = SourceDTO(
        id="S1", name="Helpful Warehouse", node_id="SRC", verified=True, partner_org="o",
        inventory=[InventoryLineDTO(resource="Food", unit="kg", available=500)],
    )
    tiny_vehicle = VehicleDTO(id="V1", partner="p", type="Motorbike", capacity_kg=10, node_id="SRC", status="Available")

    _, unmet, _ = run_allocation([req], [source], [tiny_vehicle], graph, WEIGHTS, 0.6, NOW)

    assert unmet[0].alternative_source_name == "Helpful Warehouse"
    assert unmet[0].alternative_eta is not None
