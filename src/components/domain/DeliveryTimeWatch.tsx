import { Clock3 } from "lucide-react";
import type { Delivery } from "@/types";
import { deliveryTimeTier, formatCountdown, formatTime, minutesUntil } from "@/lib/utils";
import { Badge, type BadgeTone } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/States";

const TIER_TONE: Record<ReturnType<typeof deliveryTimeTier>, BadgeTone> = {
  "On Track": "primary",
  "Approaching Deadline": "warning",
  "Deadline At Risk": "critical",
};

interface DeliveryTimeWatchProps {
  deliveries: Delivery[];
  onSelect?: (delivery: Delivery) => void;
  limit?: number;
}

/**
 * Compact dashboard widget (section 3): the most time-sensitive ACTIVE
 * deliveries, ranked by remaining time to deadline. Every value here is
 * derived from the delivery's real etaIso/deadlineIso/meetsDeadline —
 * nothing is hardcoded, and the tiering reuses the same thresholds as
 * DeadlineIndicator (see `deliveryTimeTier`), not a second definition of
 * "at risk".
 */
export function DeliveryTimeWatch({ deliveries, onSelect, limit = 5 }: DeliveryTimeWatchProps) {
  const active = deliveries
    .filter((d) => d.status !== "Delivered")
    .map((d) => ({ delivery: d, tier: deliveryTimeTier(d.deadlineIso, d.etaIso, d.meetsDeadline), minsLeft: minutesUntil(d.deadlineIso) }))
    .sort((a, b) => a.minsLeft - b.minsLeft)
    .slice(0, limit);

  if (active.length === 0) {
    return <EmptyState title="No active deliveries to watch" className="py-6" />;
  }

  return (
    <div className="flex flex-col divide-y divide-border rounded-sm border border-border bg-surface shadow-card">
      {active.map(({ delivery, tier }) => (
        <button
          key={delivery.id}
          onClick={() => onSelect?.(delivery)}
          className="flex items-center justify-between gap-3 px-3.5 py-2.5 text-left hover:bg-surface-sunken"
        >
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-text">
              {delivery.id} <span className="font-normal text-muted">→ {delivery.destinationName}</span>
            </p>
            <p className="text-[11px] text-muted tabular">
              ETA {formatTime(delivery.etaIso)} · Deadline {formatTime(delivery.deadlineIso)}
            </p>
          </div>
          <div className="flex flex-none items-center gap-2">
            <span className="flex items-center gap-1 text-[11px] text-muted tabular">
              <Clock3 className="h-3 w-3" strokeWidth={1.75} />
              {formatCountdown(delivery.deadlineIso)}
            </span>
            <Badge tone={TIER_TONE[tier]}>{tier}</Badge>
          </div>
        </button>
      ))}
    </div>
  );
}
