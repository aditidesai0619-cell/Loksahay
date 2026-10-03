"""Records a `PlanSnapshot` row reflecting the REAL persisted state of the
system at this moment (not a hypothetical engine re-run) — this is what
gives Analytics' history trend genuine data points tied to real actions
(allocation runs, replans applied, scenarios applied) instead of
fabricated numbers.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AffectedRequest, Allocation, Delivery, PlanSnapshot
from app.utils.time import now as time_now

COMMITTED_STATUSES = ("Accepted", "Modified")


def compute_live_metrics(db: Session) -> dict:
    requests = db.query(AffectedRequest).all()
    total_required = sum(r.required for r in requests) or 1.0
    total_allocated = sum(r.allocated for r in requests)

    critical = [r for r in requests if r.urgency == "Critical"]
    critical_required = sum(r.required for r in critical) or 1.0
    critical_allocated = sum(r.allocated for r in critical)

    committed = db.query(Allocation).filter(Allocation.status.in_(COMMITTED_STATUSES)).all()
    on_time = sum(1 for a in committed if a.meets_deadline)
    on_time_pct = round((on_time / len(committed)) * 100, 1) if committed else 100.0

    trips = db.query(Delivery).count()

    return {
        "demand_fulfilled_pct": round((total_allocated / total_required) * 100, 1),
        "critical_demand_fulfilled_pct": round((critical_allocated / critical_required) * 100, 1) if critical else 100.0,
        "on_time_delivery_pct": on_time_pct,
        "total_distance_km": round(sum(a.distance_km for a in committed), 1),
        "vehicle_trips": trips,
        "unmet_demand_units": round(sum(max(0.0, r.required - r.allocated) for r in requests), 1),
    }


def record_snapshot(db: Session, *, label: str) -> PlanSnapshot:
    metrics = compute_live_metrics(db)
    snapshot = PlanSnapshot(timestamp=time_now(), label=label, **metrics)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
