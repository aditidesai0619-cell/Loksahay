import { formatCountdown, formatTime, minutesUntil, cn } from "@/lib/utils";

interface DeadlineIndicatorProps {
  deadlineIso: string;
  etaIso?: string;
  // Override the "at risk" heuristic with the backend's own feasibility
  // flag (Allocation/Delivery.meetsDeadline) when one is available, so the
  // UI never disagrees with what the algorithm actually decided. Falls
  // back to a local ETA-vs-deadline buffer heuristic only when no
  // backend flag applies (e.g. a bare AffectedRequest with no allocation yet).
  atRisk?: boolean;
  className?: string;
}

export function DeadlineIndicator({ deadlineIso, etaIso, atRisk, className }: DeadlineIndicatorProps) {
  const minsLeft = minutesUntil(deadlineIso);
  const computedAtRisk = etaIso ? minutesUntil(deadlineIso) - minutesUntil(etaIso) < 20 : minsLeft < 60;
  const isAtRisk = atRisk ?? computedAtRisk;
  const overdue = minsLeft < 0;

  const tone = overdue ? "text-critical" : isAtRisk ? "text-accent-dark" : "text-secondary";

  return (
    <div className={cn("flex flex-col", className)}>
      <span className={cn("text-xs font-semibold tabular", tone)}>{formatCountdown(deadlineIso)}</span>
      <span className="text-[11px] text-muted tabular">by {formatTime(deadlineIso)}</span>
    </div>
  );
}
