"""Pure mutation functions applied to a DTO clone for scenario simulation
(section 22). Each hypothetical action type from the frontend
(`ScenarioControlType`) maps to exactly one of these.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.algorithms.dto import EdgeDTO, RequestDTO, SourceDTO, VehicleDTO
from app.utils.time import minutes_from_now


@dataclass
class ScenarioActionInput:
    type: str  # ScenarioControlType
    target_id: str
    target_label: str
    value: float | None = None


def apply_block_road(edges: list[EdgeDTO], edge_id: str) -> None:
    for e in edges:
        if e.id == edge_id:
            e.condition = "BLOCKED"
            e.blocked_reason = e.blocked_reason or "Blocked (scenario simulation)"


def apply_remove_vehicle(vehicles: list[VehicleDTO], vehicle_id: str) -> None:
    for v in vehicles:
        if v.id == vehicle_id:
            v.status = "Unavailable"


def apply_reduce_inventory(sources: list[SourceDTO], source_id: str, pct: float) -> None:
    factor = max(0.0, 1.0 - pct / 100.0)
    for s in sources:
        if s.id == source_id:
            for line in s.inventory:
                line.available = round(line.available * factor, 2)


# Synthetic defaults for a freshly-reported area (the frontend's Scenario
# Simulator offers a fixed set of candidate areas without letting the
# coordinator specify resource/urgency — these are documented prototype
# assumptions for that control).
NEW_REQUEST_DEFAULTS = {"resource": "Essentials", "unit": "kits", "required": 200.0, "people_affected": 500}


def apply_add_affected_area(
    requests: list[RequestDTO], area_id: str, area_name: str, now: datetime
) -> RequestDTO:
    new_req = RequestDTO(
        id=f"SIM-{area_id}",
        area_id=area_id,
        area_name=area_name,
        resource=NEW_REQUEST_DEFAULTS["resource"],
        required=NEW_REQUEST_DEFAULTS["required"],
        unit=NEW_REQUEST_DEFAULTS["unit"],
        people_affected=NEW_REQUEST_DEFAULTS["people_affected"],
        urgency="High",
        deadline=minutes_from_now(180, now),
        created_at=now,
    )
    requests.append(new_req)
    return new_req


URGENCY_LADDER = ["Low", "Medium", "High", "Critical"]


def apply_increase_urgency(requests: list[RequestDTO], request_id: str) -> None:
    for r in requests:
        if r.id == request_id:
            idx = URGENCY_LADDER.index(r.urgency) if r.urgency in URGENCY_LADDER else 0
            r.urgency = URGENCY_LADDER[min(idx + 1, len(URGENCY_LADDER) - 1)]


def apply_action(
    action: ScenarioActionInput,
    requests: list[RequestDTO],
    sources: list[SourceDTO],
    vehicles: list[VehicleDTO],
    edges: list[EdgeDTO],
    now: datetime,
) -> None:
    if action.type == "Block Road":
        apply_block_road(edges, action.target_id)
    elif action.type == "Remove Vehicle":
        apply_remove_vehicle(vehicles, action.target_id)
    elif action.type == "Reduce Inventory":
        apply_reduce_inventory(sources, action.target_id, action.value if action.value is not None else 30.0)
    elif action.type == "Add Affected Area":
        apply_add_affected_area(requests, action.target_id, action.target_label, now)
    elif action.type == "Increase Urgency":
        apply_increase_urgency(requests, action.target_id)
    else:
        raise ValueError(f"Unknown scenario action type: {action.type}")
