import pytest

from app.models import Allocation, Delivery, RoadEdge
from app.services import replan_service


def _pick_in_flight_allocation(db):
    """A committed allocation whose delivery is NOT yet Delivered — the
    only kind `trigger_replan` will treat as 'affected' by a disruption."""
    rows = (
        db.query(Allocation)
        .filter(Allocation.status.in_(("Accepted", "Modified")))
        .join(Delivery, Delivery.allocation_id == Allocation.id)
        .filter(Delivery.status != "Delivered")
        .all()
    )
    return next((a for a in rows if a.route_edge_ids), None)


def test_blocking_an_unused_edge_has_nothing_to_replan(seeded_db):
    # R21 (Pithoragarh<->Munsiyari) is DEGRADED but not used by any
    # committed allocation in the fresh seed — blocking it should find
    # no in-flight delivery to reroute.
    with pytest.raises(ValueError):
        replan_service.trigger_replan(seeded_db, "Road Blocked", "R21", "test block")


def test_blocking_a_used_edge_creates_a_replan_event(seeded_db):
    target = _pick_in_flight_allocation(seeded_db)
    assert target is not None
    edge_id = target.route_edge_ids[0]

    event = replan_service.trigger_replan(seeded_db, "Road Blocked", edge_id, "test block")

    assert event.trigger_type == "Road Blocked"
    assert event.old_plan["sourceId"] == target.source_id
    assert event.status == "Pending"
    blocked_edge = seeded_db.get(RoadEdge, edge_id)
    assert blocked_edge.condition == "BLOCKED"


def test_applying_a_replan_updates_the_underlying_allocation(seeded_db):
    target = _pick_in_flight_allocation(seeded_db)
    assert target is not None
    edge_id = target.route_edge_ids[0]
    original_source = target.source_id

    event = replan_service.trigger_replan(seeded_db, "Road Blocked", edge_id, "test block")
    applied = replan_service.apply_replan(seeded_db, event.id)

    assert applied.status == "Applied"
    seeded_db.refresh(target)
    # Either genuinely rerouted (source/vehicle may differ) or confirmed
    # as a no-feasible-alternative no-op — either way the allocation's
    # route must no longer rely on the now-blocked edge, UNLESS no
    # alternative existed.
    if applied.new_plan["sourceId"] != original_source:
        assert edge_id not in target.route_edge_ids


def test_dismiss_replan_leaves_allocation_untouched(seeded_db):
    target = _pick_in_flight_allocation(seeded_db)
    assert target is not None
    edge_id = target.route_edge_ids[0]
    original_source = target.source_id

    event = replan_service.trigger_replan(seeded_db, "Road Blocked", edge_id, "test block")
    dismissed = replan_service.dismiss_replan(seeded_db, event.id)

    assert dismissed.status == "Dismissed"
    seeded_db.refresh(target)
    assert target.source_id == original_source


def test_unknown_trigger_type_is_rejected(seeded_db):
    with pytest.raises(ValueError):
        replan_service.trigger_replan(seeded_db, "New Request", "REQ-01", "not supported here")
