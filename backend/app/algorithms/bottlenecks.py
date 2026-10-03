"""Bottleneck detection (section 20).

Groups unmet demand by its classified reason into one of the five
bottleneck types the frontend already renders (`BottleneckType`), and
generates a suggested action that references the real entities involved
— never a hardcoded sentence independent of the actual data.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.algorithms.dto import RequestDTO, SourceDTO, UnmetDemandDTO, VehicleDTO

REASON_TO_BOTTLENECK = {
    "No feasible vehicle": "Vehicle Capacity",
    "Road inaccessible": "Road Access",
    "Deadline infeasible": "Deadline Constraint",
    "Source unavailable": "Source Availability",
    # "Insufficient inventory" is split by resource below.
}


@dataclass
class BottleneckDTO:
    id: str
    type: str
    impact: str
    affected_request_ids: list[str]
    suggested_action: str


def _impact_for(requests: list[RequestDTO]) -> str:
    urgencies = {r.urgency for r in requests}
    if "Critical" in urgencies:
        return "Critical"
    if "High" in urgencies:
        return "High"
    return "Medium"


def detect_bottlenecks(
    requests_by_id: dict[str, RequestDTO],
    unmet: list[UnmetDemandDTO],
    sources: list[SourceDTO],
    vehicles: list[VehicleDTO],
) -> list[BottleneckDTO]:
    groups: dict[str, list[UnmetDemandDTO]] = {}
    for u in unmet:
        req = requests_by_id[u.request_id]
        if u.reason == "Insufficient inventory":
            key = "Medicine Shortage" if req.resource == "Medicine" else "Source Availability"
        else:
            key = REASON_TO_BOTTLENECK.get(u.reason, "Source Availability")
        groups.setdefault(key, []).append(u)

    results: list[BottleneckDTO] = []
    for i, (bottleneck_type, items) in enumerate(groups.items(), start=1):
        affected_requests = [requests_by_id[u.request_id] for u in items]
        affected_ids = [r.id for r in affected_requests]
        impact = _impact_for(affected_requests)
        suggested_action = _suggest_action(bottleneck_type, affected_requests, sources, vehicles)
        results.append(
            BottleneckDTO(
                id=f"BTL-{i:02d}",
                type=bottleneck_type,
                impact=impact,
                affected_request_ids=affected_ids,
                suggested_action=suggested_action,
            )
        )
    return results


def _suggest_action(
    bottleneck_type: str,
    affected_requests: list[RequestDTO],
    sources: list[SourceDTO],
    vehicles: list[VehicleDTO],
) -> str:
    resources = sorted({r.resource for r in affected_requests})
    area_names = ", ".join(r.area_name for r in affected_requests[:3])

    if bottleneck_type == "Medicine Shortage":
        low_stock = [s.name for s in sources if s.line_for("Medicine") and s.line_for("Medicine").remaining < 20]  # type: ignore[union-attr]
        detail = f" Low remaining stock at: {', '.join(low_stock)}." if low_stock else ""
        return f"Expedite medicine resupply for {area_names}.{detail}"

    if bottleneck_type == "Vehicle Capacity":
        unavailable = [v.id for v in vehicles if v.status == "Unavailable"]
        idle = [v.id for v in vehicles if v.status == "Available" and v.trips == 0]
        if idle:
            return f"Reassign idle vehicle(s) {', '.join(idle)} to cover {area_names}."
        if unavailable:
            return f"Restore or replace unavailable vehicle(s) {', '.join(unavailable)} to free capacity for {area_names}."
        return f"Add vehicle capacity on the {', '.join(resources)} lane to cover {area_names}."

    if bottleneck_type == "Road Access":
        return f"Monitor blocked/degraded segments affecting the route(s) to {area_names}; consider a detour or temporary repair."

    if bottleneck_type == "Deadline Constraint":
        return f"Ground ETA exceeds the deadline for {area_names} — escalate to an expedited or air option."

    return f"Verify or activate a backup {', '.join(resources)} source for {area_names}."
