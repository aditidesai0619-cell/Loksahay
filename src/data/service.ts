// Live service / API layer.
//
// This is the only module UI code should import domain data through. It
// calls the real LokSahay backend (FastAPI + SQLite + the greedy/graph
// allocation engine) over HTTP. The function signatures here are
// unchanged from the original mock implementation, so no component
// changes were needed to switch from mock data to a real backend.

import type {
  AffectedRequest,
  Allocation,
  AllocationStatus,
  AlgorithmSnapshot,
  AnalyticsResult,
  Bottleneck,
  Coordinator,
  Delivery,
  DeliveryPartner,
  DeliveryStatus,
  OperationalSummary,
  PriorityWeights,
  ReplanEvent,
  RoadEdge,
  RoadNode,
  Route,
  ScenarioAction,
  ScenarioResult,
  SupplySource,
  Vehicle,
} from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body?.error?.message ?? body?.detail ?? message;
    } catch {
      // ignore — fall back to statusText
    }
    throw new ApiError(message, res.status);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

async function requestOrUndefined<T>(path: string): Promise<T | undefined> {
  try {
    return await request<T>(path);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return undefined;
    throw err;
  }
}

interface RoadsResponse {
  nodes: RoadNode[];
  edges: RoadEdge[];
}

export const service = {
  getRegionMeta: () => request<{ region: string; center: { lat: number; lng: number }; zoom: number }>("/system/region"),

  getOperationalSummary: () => request<OperationalSummary>("/system/summary"),
  getAlgorithmSnapshot: () => request<AlgorithmSnapshot>("/algorithm/config"),
  getCoordinator: () => request<Coordinator>("/system/coordinator"),

  getAffectedRequests: (): Promise<AffectedRequest[]> => request("/requests"),
  getRequestById: (id: string): Promise<AffectedRequest | undefined> => requestOrUndefined(`/requests/${id}`),

  getSupplySources: (): Promise<SupplySource[]> => request("/sources"),
  getSourceById: (id: string): Promise<SupplySource | undefined> => requestOrUndefined(`/sources/${id}`),

  getVehicles: (): Promise<Vehicle[]> => request("/vehicles"),
  getVehicleById: (id: string): Promise<Vehicle | undefined> => requestOrUndefined(`/vehicles/${id}`),

  getAllocations: (): Promise<Allocation[]> => request("/allocations"),
  decideAllocation: async (
    id: string,
    decision: Extract<AllocationStatus, "Accepted" | "Modified" | "Rejected">,
    modifiedQuantity?: number,
  ): Promise<Allocation | undefined> => {
    if (decision === "Accepted") return request(`/allocations/${id}/accept`, { method: "POST" });
    if (decision === "Rejected") return request(`/allocations/${id}/reject`, { method: "POST" });
    return request(`/allocations/${id}/modify`, {
      method: "POST",
      body: JSON.stringify({ quantity: modifiedQuantity }),
    });
  },

  getDeliveries: (): Promise<Delivery[]> => request("/deliveries"),
  getDeliveryById: (id: string): Promise<Delivery | undefined> => requestOrUndefined(`/deliveries/${id}`),

  getPartners: (): Promise<DeliveryPartner[]> => request("/partners"),
  getPartnerById: (id: string): Promise<DeliveryPartner | undefined> => requestOrUndefined(`/partners/${id}`),

  getRoadNodes: async (): Promise<RoadNode[]> => (await request<RoadsResponse>("/roads")).nodes,
  getRoadEdges: async (): Promise<RoadEdge[]> => (await request<RoadsResponse>("/roads")).edges,
  getRoutes: (): Promise<Route[]> => request("/routes"),
  getRouteById: (id: string): Promise<Route | undefined> => requestOrUndefined(`/routes/${id}`),

  getBottlenecks: (): Promise<Bottleneck[]> => request("/bottlenecks"),

  getReplanEvents: (): Promise<ReplanEvent[]> => request("/replan"),
  applyReplan: (id: string): Promise<ReplanEvent | undefined> => request(`/replan/${id}/apply`, { method: "POST" }),
  dismissReplan: (id: string): Promise<ReplanEvent | undefined> => request(`/replan/${id}/dismiss`, { method: "POST" }),

  getAnalytics: (): Promise<AnalyticsResult> => request("/analytics"),

  runScenario: (actions: ScenarioAction[]): Promise<ScenarioResult> =>
    request("/scenario/simulate", { method: "POST", body: JSON.stringify({ actions }) }),
  applyScenario: (actions: ScenarioAction[]): Promise<ScenarioResult> =>
    request("/scenario/apply", { method: "POST", body: JSON.stringify({ actions }) }),

  advanceDeliveryStatus: (id: string, status: DeliveryStatus, note?: string): Promise<Delivery> =>
    request(`/deliveries/${id}/status`, { method: "POST", body: JSON.stringify({ status, note }) }),

  updateAlgorithmWeights: (weights: Partial<PriorityWeights> & { minimumCoveragePct?: number }): Promise<AlgorithmSnapshot> =>
    request("/algorithm/config", {
      method: "PUT",
      body: JSON.stringify({
        urgencyWeight: weights.urgency,
        populationNeedWeight: weights.populationNeed,
        supplyDeficitWeight: weights.supplyDeficit,
        accessibilityWeight: weights.accessibility,
        minimumCoveragePct: weights.minimumCoveragePct,
      }),
    }),

  resetDemo: (): Promise<OperationalSummary> => request("/system/reset-demo", { method: "POST" }),
};
