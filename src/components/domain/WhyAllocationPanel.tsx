import { CircleCheck } from "lucide-react";
import type { Allocation } from "@/types";

const BREAKDOWN_ROWS: { key: keyof NonNullable<Allocation["priorityBreakdown"]>; label: string }[] = [
  { key: "urgencyScore", label: "Urgency" },
  { key: "populationNeedScore", label: "Population Need" },
  { key: "supplyDeficitScore", label: "Supply Deficit" },
  { key: "accessibilityScore", label: "Accessibility" },
];

export function WhyAllocationPanel({ allocation }: { allocation: Allocation }) {
  return (
    <div className="rounded-sm border border-border bg-surface-sunken p-3.5 shadow-card">
      <p className="mb-2 text-xs font-semibold text-text">Why this allocation?</p>
      <ul className="flex flex-col gap-1.5">
        {allocation.reasons.map((reason, i) => (
          <li key={i} className="flex items-start gap-2 text-xs text-secondary">
            <CircleCheck className="mt-0.5 h-3.5 w-3.5 flex-none text-primary" strokeWidth={1.75} />
            <span>{reason}</span>
          </li>
        ))}
      </ul>

      {allocation.priorityBreakdown && (
        <div className="mt-3 border-t border-border pt-3">
          <div className="mb-1.5 flex items-center justify-between">
            <p className="text-[11px] font-medium uppercase tracking-wide text-muted">
              Priority Score: {allocation.priorityScore.toFixed(2)}
            </p>
            <span className="text-[10px] text-muted">prototype, configurable priority model</span>
          </div>
          <div className="flex flex-col gap-1.5">
            {BREAKDOWN_ROWS.map(({ key, label }) => {
              const value = allocation.priorityBreakdown![key];
              const pct = Math.round(value * 100);
              return (
                <div key={key} className="flex items-center gap-2.5">
                  <span className="w-28 flex-none text-[11px] text-secondary">{label}</span>
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="w-8 flex-none text-right text-[11px] tabular text-text">{pct}%</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
