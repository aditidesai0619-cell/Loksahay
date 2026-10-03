import { AlertOctagon } from "lucide-react";
import type { Bottleneck } from "@/types";
import { bottleneckImpactTone } from "@/lib/utils";
import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/States";

export function BottleneckPanel({ bottlenecks }: { bottlenecks: Bottleneck[] }) {
  if (bottlenecks.length === 0) {
    return <EmptyState title="No active bottlenecks" description="The network is currently operating within feasible limits." />;
  }

  return (
    <div className="flex flex-col gap-2.5">
      {bottlenecks.map((b) => (
        <div key={b.id} className="flex gap-3 rounded-sm border border-border bg-surface p-3.5 shadow-card">
          <AlertOctagon className="mt-0.5 h-4 w-4 flex-none text-critical" strokeWidth={1.75} />
          <div className="flex-1">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-text">{b.type}</p>
              <Badge tone={bottleneckImpactTone(b.impact)}>{b.impact}</Badge>
            </div>
            <p className="mt-1 text-[11px] text-muted">
              Affects {b.affectedRequestIds.length} request{b.affectedRequestIds.length === 1 ? "" : "s"}: {b.affectedRequestIds.join(", ")}
            </p>
            <p className="mt-1.5 text-xs text-secondary">{b.suggestedAction}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
