// Core domain models for LokSahay — the algorithmic disaster-relief
// resource allocation, transport coordination and dynamic replanning system.
// These types describe the contract between the UI and the real backend
// (FastAPI + SQLAlchemy + the greedy/graph allocation engine). `service.ts`
// calls that backend directly over HTTP — nothing here is mock data.

export type ResourceType = "Food" | "Medicine" | "Water" | "Essentials";

export type UrgencyLevel = "Critical" | "High" | "Medium" | "Low";

export type RequestStatus = "Unfulfilled" | "Partial" | "Fulfilled";

export type UnmetReason =
  | "Insufficient inventory"
  | "No feasible vehicle"
  | "Road inaccessible"
  | "Deadline infeasible"
  | "Source unavailable";

export interface LatLng {
  lat: number;
  lng: number;
}

export interface AffectedRequest {
  id: string;
  areaId: string;
  areaName: string;
  location: LatLng;
  resource: ResourceType;
  required: number;
  unit: string;
  allocated: number;
  peopleAffected: number;
  urgency: UrgencyLevel;
  deadline: string; // ISO timestamp
  status: RequestStatus;
  reason?: UnmetReason;
  alternativeSourceName?: string;
  alternativeEtaIso?: string;
  createdAt: string;
}

export type SourceType = "Warehouse" | "Hospital" | "Relief Depot" | "Community Stock";

export interface InventoryLine {
  resource: ResourceType;
  unit: string;
  available: number;
  allocated: number;
  delivered: number;
}

export interface SupplySource {
  id: string;
  name: string;
  type: SourceType;
  location: LatLng;
  verified: boolean;
  inventory: InventoryLine[];
  partnerOrg: string;
}

export type VehicleStatus = "Available" | "Assigned" | "In Transit" | "Delivered" | "Unavailable";

export interface CargoLine {
  resource: ResourceType;
  quantity: number;
  unit: string;
}

export interface Vehicle {
  id: string;
  partner: string;
  type: "Truck" | "Mini-Van" | "4x4" | "Motorbike";
  capacityKg: number;
  cargo: CargoLine[];
  cargoWeightKg: number;
  location: LatLng;
  status: VehicleStatus;
  currentDeliveryId?: string;
}

export type RoadCondition = "Clear" | "Degraded" | "Blocked";

export interface RoadNode {
  id: string;
  name: string;
  location: LatLng;
}

export interface RoadEdge {
  id: string;
  from: string; // RoadNode id
  to: string; // RoadNode id
  distanceKm: number;
  condition: RoadCondition;
  blockedReason?: string;
}

export interface Route {
  id: string;
  nodeIds: string[];
  edgeIds: string[];
  distanceKm: number;
  etaMinutes: number;
  path: LatLng[];
  feasible: boolean;
}

export type AllocationStatus = "Proposed" | "Accepted" | "Modified" | "Rejected";

export interface PriorityBreakdown {
  urgencyScore: number;
  populationNeedScore: number;
  supplyDeficitScore: number;
  accessibilityScore: number;
}

export interface Allocation {
  id: string;
  requestId: string;
  sourceId: string;
  vehicleId: string;
  routeId: string;
  resource: ResourceType;
  quantity: number;
  unit: string;
  etaIso: string;
  deadlineIso: string;
  status: AllocationStatus;
  reasons: string[];
  meetsDeadline: boolean;
  priorityScore: number;
  priorityBreakdown?: PriorityBreakdown;
}

export type DeliveryStatus =
  | "Assigned"
  | "Accepted"
  | "Picked Up"
  | "In Transit"
  | "Arrived"
  | "Delivered";

export interface TrackingEvent {
  id: string;
  status: DeliveryStatus;
  timestamp: string;
  note?: string;
  location?: LatLng;
}

export interface Delivery {
  id: string;
  allocationId: string;
  vehicleId: string;
  requestId: string;
  sourceId: string;
  routeId: string;
  cargo: CargoLine[];
  originName: string;
  destinationName: string;
  distanceKm: number;
  etaIso: string;
  deadlineIso: string;
  meetsDeadline: boolean;
  status: DeliveryStatus;
  // Location of the most recent tracking event — controlled/simulated
  // (a waypoint along the planned route keyed to lifecycle stage), not
  // real GPS tracking.
  currentLocation?: LatLng;
  events: TrackingEvent[];
}

export interface PartnerVehicleSummary {
  vehicleId: string;
  type: "Truck" | "Mini-Van" | "4x4" | "Motorbike";
  capacityKg: number;
  status: VehicleStatus;
  currentDeliveryId?: string;
}

export interface DeliveryPartner {
  id: string;
  name: string;
  contactPerson: string;
  phone: string;
  vehicles: PartnerVehicleSummary[];
  completedDeliveries: number;
  activeDeliveries: number;
}

export interface ReplanPlanSnapshot {
  sourceId: string;
  sourceName: string;
  vehicleId: string;
  routeId: string;
  routeLabel: string;
  etaIso: string;
}

export type ReplanStatus = "Pending" | "Applied" | "Dismissed";

export interface ReplanEvent {
  id: string;
  triggeredAt: string;
  triggerDescription: string;
  triggerType: "Road Blocked" | "Vehicle Unavailable" | "Inventory Shortfall" | "New Request";
  affectedDeliveryIds: string[];
  vehiclesAffectedCount: number;
  deadlinesAtRiskCount: number;
  oldPlan: ReplanPlanSnapshot;
  newPlan: ReplanPlanSnapshot;
  alternativesConsidered: string[];
  status: ReplanStatus;
  metricsBefore?: ScenarioMetrics;
  metricsAfter?: ScenarioMetrics;
}

export type ScenarioControlType =
  | "Block Road"
  | "Remove Vehicle"
  | "Reduce Inventory"
  | "Add Affected Area"
  | "Increase Urgency";

export interface ScenarioAction {
  id: string;
  type: ScenarioControlType;
  targetId: string;
  targetLabel: string;
  value?: number;
}

export interface ScenarioMetrics {
  demandFulfilledPct: number;
  criticalDemandFulfilledPct: number;
  onTimeDeliveryPct: number;
  totalDistanceKm: number;
  vehicleTrips: number;
  unmetDemandUnits: number;
}

export interface ScenarioResult {
  id: string;
  actions: ScenarioAction[];
  before: ScenarioMetrics;
  after: ScenarioMetrics;
  changedAllocations: number;
  changedRoutes: number;
  affectedDeliveryIds: string[];
  newBottlenecks: Bottleneck[];
  generatedAt: string;
}

export interface AlgorithmComparisonResult {
  label: string;
  metrics: ScenarioMetrics;
}

export interface AnalyticsResult {
  current: ScenarioMetrics;
  loksahay: AlgorithmComparisonResult;
  baseline: AlgorithmComparisonResult;
  history: { timestamp: string; demandFulfilledPct: number; onTimeDeliveryPct: number }[];
}

export type BottleneckType =
  | "Vehicle Capacity"
  | "Medicine Shortage"
  | "Road Access"
  | "Source Availability"
  | "Deadline Constraint";

export type BottleneckImpact = "Critical" | "High" | "Medium";

export interface Bottleneck {
  id: string;
  type: BottleneckType;
  impact: BottleneckImpact;
  affectedRequestIds: string[];
  suggestedAction: string;
}

export interface PriorityWeights {
  urgency: number;
  populationNeed: number;
  supplyDeficit: number;
  accessibility: number;
}

export interface AlgorithmSnapshot {
  requestsEvaluated: number;
  verifiedSources: number;
  availableVehicles: number;
  feasibleRoutes: number;
  minimumCoveragePct: number;
  planGeneratedAt: string;
  priorityWeights: PriorityWeights;
}

export interface OperationalSummary {
  region: string;
  systemStatus: "Operational" | "Degraded" | "Offline";
  lastPlanGeneratedAt: string;
  criticalNeeds: number;
  activeDeliveries: number;
  resourceCoveragePct: number;
  vehiclesAvailable: number;
  atRiskDeliveries: number;
}

export interface Coordinator {
  name: string;
  role: string;
  region: string;
  initials: string;
}
