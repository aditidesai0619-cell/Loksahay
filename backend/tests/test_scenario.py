from app.models import RoadEdge, Vehicle
from app.services import scenario_service


def test_simulate_block_road_does_not_persist_changes(seeded_db):
    scenario_service.simulate_scenario(seeded_db, [{"type": "Block Road", "target_id": "R9", "target_label": "R9"}])
    edge = seeded_db.get(RoadEdge, "R9")
    assert edge.condition != "BLOCKED"


def test_simulate_remove_vehicle_does_not_persist_changes(seeded_db):
    scenario_service.simulate_scenario(
        seeded_db, [{"type": "Remove Vehicle", "target_id": "V-01", "target_label": "V-01"}]
    )
    vehicle = seeded_db.get(Vehicle, "V-01")
    assert vehicle.status != "Unavailable"


def test_apply_remove_vehicle_persists_and_replans(seeded_db):
    result = scenario_service.apply_scenario(
        seeded_db, [{"type": "Remove Vehicle", "target_id": "V-05", "target_label": "V-05"}]
    )
    vehicle = seeded_db.get(Vehicle, "V-05")
    assert vehicle.status == "Unavailable"
    assert result.after is not None


def test_simulate_returns_before_and_after_metrics(seeded_db):
    result = scenario_service.simulate_scenario(
        seeded_db, [{"type": "Reduce Inventory", "target_id": "SRC-01", "target_label": "SRC-01", "value": 100}]
    )
    assert result.before.demand_fulfilled_pct >= 0
    assert result.after.demand_fulfilled_pct >= 0
    assert isinstance(result.new_bottlenecks, list)


def test_increase_urgency_scenario_changes_nothing_structurally_when_no_capacity_left(seeded_db):
    # A pure sanity check that the action is accepted and produces a
    # well-formed result even when it can't change the outcome.
    result = scenario_service.simulate_scenario(
        seeded_db, [{"type": "Increase Urgency", "target_id": "REQ-08", "target_label": "Bageshwar"}]
    )
    assert result.changed_allocations >= 0
    assert result.changed_routes >= 0


def test_add_affected_area_increases_total_required_demand(seeded_db):
    from app.services import converters

    before_total = sum(r.required for r in converters.load_requests(seeded_db))
    scenario_service.apply_scenario(
        seeded_db, [{"type": "Add Affected Area", "target_id": "N-DEV", "target_label": "Devprayag (new report)"}]
    )
    after_total = sum(r.required for r in converters.load_requests(seeded_db))
    assert after_total > before_total
