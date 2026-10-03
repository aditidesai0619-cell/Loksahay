import type { AlgorithmSnapshot } from "@/types";
import { formatDateTime } from "@/lib/utils";
import { Badge } from "@/components/common/Badge";

const WEIGHT_ROWS: { key: keyof AlgorithmSnapshot["priorityWeights"]; label: string }[] = [
  { key: "urgency", label: "Urgency" },
  { key: "populationNeed", label: "Population Need" },
  { key: "supplyDeficit", label: "Supply Deficit" },
  { key: "accessibility", label: "Accessibility" },
];

export function AlgorithmPanel({ snapshot }: { snapshot: AlgorithmSnapshot }) {
  return (
    <div className="flex flex-col gap-4 rounded-sm border border-border bg-surface p-4 shadow-card">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-text">Algorithm Intelligence</h3>
          <p className="text-[11px] text-muted">Allocation Engine · priority + feasibility model</p>
        </div>
        <Badge tone="secondary">Prototype</Badge>
      </div>

      <dl className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-3">
        <Stat label="Requests Evaluated" value={snapshot.requestsEvaluated} />
        <Stat label="Verified Sources" value={snapshot.verifiedSources} />
        <Stat label="Available Vehicles" value={snapshot.availableVehicles} />
        <Stat label="Feasible Routes" value={snapshot.feasibleRoutes} />
        <Stat label="Min. Coverage" value={`${snapshot.minimumCoveragePct}%`} />
        <Stat label="Plan Generated" value={formatDateTime(snapshot.planGeneratedAt)} />
      </dl>

      <div>
        <div className="mb-2 flex items-center justify-between">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted">Priority Model</p>
          <span className="text-[10px] text-muted">configurable weights</span>
        </div>
        <div className="flex flex-col gap-2">
          {WEIGHT_ROWS.map((row) => {
            const pct = Math.round(snapshot.priorityWeights[row.key] * 100);
            return (
              <div key={row.key} className="flex items-center gap-2.5">
                <span className="w-32 flex-none text-xs text-secondary">{row.label}</span>
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-sunken">
                  <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
                </div>
                <span className="w-9 flex-none text-right text-xs tabular text-text">{pct}%</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-[10px] uppercase tracking-wide text-muted">{label}</dt>
      <dd className="text-sm font-semibold tabular text-text">{value}</dd>
    </div>
  );
}
