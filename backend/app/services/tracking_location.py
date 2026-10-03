"""Shared helper for populating TrackingEvent.lat/lng (columns that already
existed on the model but were never written to). Reused by
`allocation_service` (the initial "Assigned" event) and `delivery_service`
(every subsequent lifecycle transition) so a delivery's "current/last known
location" is simply the most recent tracking event's coordinates — no new
columns, no duplicate location-tracking logic.

This is deliberately simple, controlled/simulated movement (a node along
the delivery's already-computed route, picked by lifecycle stage) — not a
claim of real GPS tracking, which this system does not have.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

# Which point along route_node_ids a delivery is considered "at" for a
# given lifecycle stage.
_STAGE_POSITION = {
    "Assigned": "origin",
    "Accepted": "origin",
    "Picked Up": "origin",
    "In Transit": "midpoint",
    "Arrived": "destination",
    "Delivered": "destination",
}


def location_for_stage(db: Session, route_node_ids: list[str], stage: str) -> tuple[float, float] | None:
    if not route_node_ids:
        return None
    from app.models import RoadNode

    position = _STAGE_POSITION.get(stage, "origin")
    if position == "origin":
        node_id = route_node_ids[0]
    elif position == "destination":
        node_id = route_node_ids[-1]
    else:
        node_id = route_node_ids[len(route_node_ids) // 2]

    node = db.get(RoadNode, node_id)
    if node is None:
        return None
    return (node.lat, node.lng)
