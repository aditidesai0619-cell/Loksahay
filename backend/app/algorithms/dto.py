"""Plain dataclasses the allocation engine operates on.

The engine (`allocation_engine.py`) is a pure function over these DTOs —
it never touches the database. That is what lets the exact same engine
back both a real `/allocation/run` (persisted) and a scenario
`/scenario/simulate` preview (a disposable in-memory clone): the service
layer is the only place that converts ORM rows to/from these DTOs.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime

# Resource -> approximate kg per unit, used only to check a candidate
# shipment against vehicle capacity (frontend records quantities in mixed
# units — kg, L, kits). This is a documented prototype assumption, not a
# real logistics conversion table.
UNIT_WEIGHT_KG: dict[str, float] = {
    "Food": 1.0,
    "Water": 1.0,
    "Medicine": 0.5,
    "Essentials": 2.0,
}


def cargo_weight_kg(resource: str, quantity: float) -> float:
    return quantity * UNIT_WEIGHT_KG.get(resource, 1.0)


@dataclass
class NodeDTO:
    id: str
    name: str
    lat: float
    lng: float


@dataclass
class EdgeDTO:
    id: str
    from_id: str
    to_id: str
    distance_km: float
    condition: str  # OPEN | DEGRADED | BLOCKED
    blocked_reason: str | None = None


@dataclass
class RequestDTO:
    id: str
    area_id: str
    area_name: str
    resource: str
    required: float
    unit: str
    people_affected: int
    urgency: str
    deadline: datetime
    created_at: datetime
    allocated: float = 0.0  # mutated by the engine as it allocates

    @property
    def unmet(self) -> float:
        return max(0.0, self.required - self.allocated)


@dataclass
class InventoryLineDTO:
    resource: str
    unit: str
    available: float
    allocated: float = 0.0  # mutated by the engine as it allocates

    @property
    def remaining(self) -> float:
        return max(0.0, self.available - self.allocated)


@dataclass
class SourceDTO:
    id: str
    name: str
    node_id: str
    verified: bool
    partner_org: str
    inventory: list[InventoryLineDTO] = field(default_factory=list)

    def line_for(self, resource: str) -> InventoryLineDTO | None:
        return next((line for line in self.inventory if line.resource == resource), None)


@dataclass
class VehicleDTO:
    id: str
    partner: str
    type: str
    capacity_kg: float
    node_id: str
    status: str  # Available | Assigned | In Transit | Delivered | Unavailable
    trips: int = 0  # shipments assigned within the current engine run


@dataclass
class AllocationResultDTO:
    """One proposed/placed allocation produced by the engine."""

    request_id: str
    source_id: str
    source_name: str
    source_verified: bool
    vehicle_id: str
    resource: str
    quantity: float
    unit: str
    route_node_ids: list[str]
    route_edge_ids: list[str]
    distance_km: float
    eta_minutes: float
    eta: datetime
    deadline: datetime
    meets_deadline: bool
    priority_score: float
    reasons: list[str]


@dataclass
class UnmetDemandDTO:
    request_id: str
    required: float
    allocated: float
    unmet: float
    reason: str
    alternative_source_name: str | None = None
    alternative_eta: datetime | None = None


@dataclass
class PriorityBreakdownDTO:
    request_id: str
    priority_score: float
    urgency_score: float
    population_need_score: float
    supply_deficit_score: float
    accessibility_score: float
    explanation: str


@dataclass
class AllocationRunResult:
    allocations: list[AllocationResultDTO]
    unmet: list[UnmetDemandDTO]
    priorities: dict[str, PriorityBreakdownDTO]
    requests_evaluated: int
    feasible_route_pairs: int


def clone_requests(requests: list[RequestDTO]) -> list[RequestDTO]:
    return [replace(r) for r in requests]


def clone_sources(sources: list[SourceDTO]) -> list[SourceDTO]:
    return [replace(s, inventory=[replace(line) for line in s.inventory]) for s in sources]


def clone_vehicles(vehicles: list[VehicleDTO]) -> list[VehicleDTO]:
    return [replace(v) for v in vehicles]
