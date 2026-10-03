import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type MetricTone = "neutral" | "critical" | "warning" | "primary";

const TONE_VALUE_CLASSES: Record<MetricTone, string> = {
  neutral: "text-text",
  critical: "text-critical",
  warning: "text-accent-dark",
  primary: "text-primary",
};

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: LucideIcon;
  tone?: MetricTone;
  caption?: string;
  className?: string;
}

const TONE_ICON_WRAP_CLASSES: Record<MetricTone, string> = {
  neutral: "bg-surface-sunken text-secondary",
  critical: "bg-critical-tint text-critical",
  warning: "bg-warning-tint text-[#7a5717]",
  primary: "bg-primary-tint text-primary",
};

export function MetricCard({ label, value, unit, icon: Icon, tone = "neutral", caption, className }: MetricCardProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2.5 rounded-sm border border-border bg-surface px-4 py-3.5 shadow-card",
        className,
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-muted">{label}</span>
        {Icon && (
          <span className={cn("flex h-6 w-6 flex-none items-center justify-center rounded-md", TONE_ICON_WRAP_CLASSES[tone])}>
            <Icon className="h-3.5 w-3.5" strokeWidth={1.75} />
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className={cn("text-[26px] font-bold tabular leading-none", TONE_VALUE_CLASSES[tone])}>{value}</span>
        {unit && <span className="text-xs text-muted">{unit}</span>}
      </div>
      {caption && <span className="text-[11px] text-muted leading-tight">{caption}</span>}
    </div>
  );
}
