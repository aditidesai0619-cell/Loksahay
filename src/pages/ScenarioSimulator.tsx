import { useEffect, useMemo, useState } from "react";
import { Plus, FlaskConical, CircleCheck } from "lucide-react";
import type {
  AffectedRequest,
  Delivery,
  RoadEdge,
  ScenarioAction,
  ScenarioControlType,
  ScenarioResult,
  SupplySource,
  Vehicle,
} from "@/types";
import { service, ApiError } from "@/data/service";
import { formatNumber } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { LoadingState, ErrorState } from "@/components/common/States";
import { ScenarioControl, SCENARIO_TYPES } from "@/components/domain/ScenarioControl";
import { BottleneckPanel } from "@/components/domain/BottleneckPanel";

interface SimData {
  requests: AffectedRequest[];
  sources: SupplySource[];
  vehicles: Vehicle[];
  roadEdges: RoadEdge[];
  deliveries: Delivery[];
}

// Real road nodes seeded on the backend (backend/app/data/geo_seed.py) for
// this control — these ids must match the backend's graph exactly, or
// "Add Affected Area" silently produces an unreachable request.
const CANDIDATE_AREAS = [
  { id: "N-DEV", label: "Devprayag (new report)" },
  { id: "N-GUP", label: "Guptkashi (new report)" },
  { id: "N-MAN", label: "Mandal Valley (new report)" },
];

let actionSeq = 0;
function nextActionId() {
  actionSeq += 1;
  return `ACT-${actionSeq}`;
}

export function ScenarioSimulator() {
  const [data, setData] = useState<SimData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actions, setActions] = useState<ScenarioAction[]>([]);
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applied, setApplied] = useState(false);

  function load() {
    setLoadError(null);
    Promise.all([
      service.getAffectedRequests(),
      service.getSupplySources(),
      service.getVehicles(),
      service.getRoadEdges(),
      service.getDeliveries(),
    ])
      .then(([requests, sources, vehicles, roadEdges, deliveries]) => {
        setData({ requests, sources, vehicles, roadEdges, deliveries });
      })
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend"));
  }

  useEffect(() => {
    load();
  }, []);

  const targetOptionsFor = useMemo(() => {
    return (type: ScenarioControlType) => {
      if (!data) return [];
      switch (type) {
        case "Block Road":
          return data.roadEdges
            .filter((e) => e.condition !== "Blocked")
            .map((e) => ({ id: e.id, label: `${e.id}: ${e.from} ↔ ${e.to} (${e.distanceKm} km)` }));
        case "Remove Vehicle":
          return data.vehicles
            .filter((v) => v.status !== "Unavailable")
            .map((v) => ({ id: v.id, label: `${v.id} · ${v.partner} (${v.status})` }));
        case "Reduce Inventory":
          return data.sources.map((s) => ({ id: s.id, label: s.name }));
        case "Add Affected Area":
          return CANDIDATE_AREAS;
        case "Increase Urgency":
          return data.requests
            .filter((r) => r.urgency !== "Critical")
            .map((r) => ({ id: r.id, label: `${r.id} · ${r.areaName} (${r.urgency})` }));
      }
    };
  }, [data]);

  function addAction() {
    const type = SCENARIO_TYPES[0];
    setActions((prev) => [...prev, { id: nextActionId(), type, targetId: "", targetLabel: "" }]);
    setResult(null);
    setApplied(false);
  }

  function updateAction(id: string, patch: Partial<ScenarioAction>) {
    setActions((prev) => prev.map((a) => (a.id === id ? { ...a, ...patch } : a)));
    setResult(null);
    setApplied(false);
  }

  function removeAction(id: string) {
    setActions((prev) => prev.filter((a) => a.id !== id));
    setResult(null);
    setApplied(false);
  }

  async function runReplan() {
    const valid = actions.filter((a) => a.targetId);
    if (valid.length === 0) return;
    setRunning(true);
    setRunError(null);
    setApplied(false);
    try {
      const res = await service.runScenario(valid);
      setResult(res);
    } catch (err) {
      setRunError(err instanceof ApiError ? err.message : "Simulation failed — try again");
    } finally {
      setRunning(false);
    }
  }

  async function applyScenario() {
    const valid = actions.filter((a) => a.targetId);
    if (valid.length === 0) return;
    setApplying(true);
    setApplyError(null);
    try {
      const res = await service.applyScenario(valid);
      setResult(res);
      setApplied(true);
    } catch (err) {
      setApplyError(err instanceof ApiError ? err.message : "Could not apply the scenario — try again");
    } finally {
      setApplying(false);
    }
  }

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="Scenario Simulator" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load scenario simulator" description={loadError} />
        </div>
      </div>
    );
  }

  if (!data) {
    return <LoadingState title="Loading scenario simulator…" className="h-full" />;
  }

  return (
    <div className="flex flex-col">
      <PageHeader title="Scenario Simulator" subtitle="What-if analysis against the current relief network — prototype engine" />

      <div className="flex flex-col gap-4 p-5 sm:p-6">
        <section className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-text">Scenario Controls</h2>
            <button
              onClick={addAction}
              className="flex items-center gap-1 rounded-sm border border-border px-2.5 py-1.5 text-xs font-medium text-secondary hover:bg-surface-sunken"
            >
              <Plus className="h-3.5 w-3.5" strokeWidth={1.75} />
              Add Control
            </button>
          </div>

          {actions.length === 0 ? (
            <p className="text-xs text-muted">Add one or more controls, then run the simulation to see the projected impact.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {actions.map((action) => (
                <ScenarioControl
                  key={action.id}
                  action={action}
                  targetOptions={targetOptionsFor(action.type) ?? []}
                  onTypeChange={(type) => updateAction(action.id, { type, targetId: "", targetLabel: "" })}
                  onTargetChange={(targetId, targetLabel) => updateAction(action.id, { targetId, targetLabel })}
                  onValueChange={(value) => updateAction(action.id, { value })}
                  onRemove={() => removeAction(action.id)}
                />
              ))}
            </div>
          )}

          <div className="mt-1 flex flex-wrap items-center gap-2">
            <button
              onClick={runReplan}
              disabled={running || applying || actions.every((a) => !a.targetId)}
              className="flex w-fit items-center gap-1.5 rounded-sm bg-primary px-3.5 py-2 text-xs font-semibold text-background hover:bg-primary-dark disabled:cursor-not-allowed disabled:opacity-50"
            >
              <FlaskConical className="h-3.5 w-3.5" strokeWidth={1.75} />
              {running ? "Running Simulation…" : "RUN SIMULATION"}
            </button>
            {result && !applied && (
              <button
                onClick={applyScenario}
                disabled={applying || running}
                className="flex w-fit items-center gap-1.5 rounded-sm border border-accent/40 bg-accent-tint px-3.5 py-2 text-xs font-semibold text-accent-dark hover:bg-accent-tint/70 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {applying ? "Applying…" : "APPLY SCENARIO"}
              </button>
            )}
            {applied && !applying && (
              <span className="flex items-center gap-1.5 text-xs font-medium text-primary">
                <CircleCheck className="h-3.5 w-3.5" strokeWidth={1.75} />
                Applied — committed to the live plan. See Replanning / Transport for the result.
              </span>
            )}
          </div>
          {runError && <p className="text-xs text-critical">{runError}</p>}
          {applyError && <p className="text-xs text-critical">{applyError}</p>}
          <p className="text-[11px] text-muted">
            Running a simulation never changes the live plan — it previews before/after on a disposable copy. Only
            Apply Scenario persists the change and re-runs the real allocation engine.
          </p>
        </section>

        {result && (
          <section className="flex flex-col gap-4 rounded-sm border border-border bg-surface p-4 shadow-card">
            <h2 className="text-sm font-semibold text-text">{applied ? "Applied Impact" : "Projected Impact"}</h2>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-sm">
                <thead>
                  <tr className="border-b border-border text-[11px] uppercase text-muted">
                    <th className="px-2 py-2 text-left">Metric</th>
                    <th className="px-2 py-2 text-right">Before</th>
                    <th className="px-2 py-2 text-right">After</th>
                  </tr>
                </thead>
                <tbody>
                  <MetricRow label="Demand Fulfilled %" before={result.before.demandFulfilledPct} after={result.after.demandFulfilledPct} suffix="%" />
                  <MetricRow
                    label="Critical Demand Fulfilled %"
                    before={result.before.criticalDemandFulfilledPct}
                    after={result.after.criticalDemandFulfilledPct}
                    suffix="%"
                  />
                  <MetricRow label="On-Time Delivery %" before={result.before.onTimeDeliveryPct} after={result.after.onTimeDeliveryPct} suffix="%" />
                  <MetricRow label="Total Distance" before={result.before.totalDistanceKm} after={result.after.totalDistanceKm} suffix=" km" />
                  <MetricRow label="Vehicle Trips" before={result.before.vehicleTrips} after={result.after.vehicleTrips} />
                  <MetricRow label="Unmet Demand (units)" before={result.before.unmetDemandUnits} after={result.after.unmetDemandUnits} inverse />
                </tbody>
              </table>
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
              <StatBlock label="Changed Allocations" value={result.changedAllocations} />
              <StatBlock label="Changed Routes" value={result.changedRoutes} />
              <StatBlock label="Affected Deliveries" value={result.affectedDeliveryIds.length} />
            </div>

            {result.affectedDeliveryIds.length > 0 && (
              <p className="text-xs text-muted">Affected: {result.affectedDeliveryIds.join(", ")}</p>
            )}

            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">New Bottlenecks</h3>
              <BottleneckPanel bottlenecks={result.newBottlenecks} />
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

function MetricRow({
  label,
  before,
  after,
  suffix = "",
  inverse = false,
}: {
  label: string;
  before: number;
  after: number;
  suffix?: string;
  inverse?: boolean;
}) {
  const improved = inverse ? after < before : after > before;
  const changed = after !== before;
  return (
    <tr className="border-b border-border last:border-0">
      <td className="px-2 py-2 text-text">{label}</td>
      <td className="px-2 py-2 text-right tabular text-muted">{formatNumber(before)}{suffix}</td>
      <td className={`px-2 py-2 text-right tabular font-medium ${changed ? (improved ? "text-primary" : "text-critical") : "text-text"}`}>
        {formatNumber(after)}{suffix}
      </td>
    </tr>
  );
}

function StatBlock({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-sm border border-border bg-surface-sunken p-3 shadow-card">
      <p className="text-lg font-semibold tabular text-text">{value}</p>
      <p className="text-[10px] uppercase tracking-wide text-muted">{label}</p>
    </div>
  );
}
