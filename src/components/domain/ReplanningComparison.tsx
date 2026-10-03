import { ArrowRight } from "lucide-react";
import type { ReplanPlanSnapshot } from "@/types";
import { formatTime, cn } from "@/lib/utils";

function PlanCard({ title, plan, tone }: { title: string; plan: ReplanPlanSnapshot; tone: "muted" | "primary" }) {
  return (
    <div
      className={cn(
        "flex flex-1 flex-col gap-2.5 rounded-sm border p-4 shadow-card",
        tone === "primary" ? "border-primary/30 bg-primary-tint/40" : "border-border bg-surface-sunken",
      )}
    >
      <p
        className={cn(
          "text-[11px] font-semibold uppercase tracking-wide",
          tone === "primary" ? "text-primary-dark" : "text-muted",
        )}
      >
        {title}
      </p>
      <dl className="flex flex-col gap-1.5 text-sm">
        <Row label="Source" value={plan.sourceName} />
        <Row label="Vehicle" value={plan.vehicleId} />
        <Row label="Route" value={plan.routeLabel} />
        <Row label="ETA" value={formatTime(plan.etaIso)} />
      </dl>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="text-[11px] text-muted">{label}</dt>
      <dd className="truncate text-right font-medium text-text">{value}</dd>
    </div>
  );
}

export function ReplanningComparison({ oldPlan, newPlan }: { oldPlan: ReplanPlanSnapshot; newPlan: ReplanPlanSnapshot }) {
  return (
    <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
      <PlanCard title="Old Plan" plan={oldPlan} tone="muted" />
      <ArrowRight className="mx-auto h-5 w-5 flex-none rotate-90 text-muted sm:rotate-0" strokeWidth={1.75} />
      <PlanCard title="New Plan" plan={newPlan} tone="primary" />
    </div>
  );
}
