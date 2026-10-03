import { ShieldCheck, ShieldAlert } from "lucide-react";
import type { SupplySource } from "@/types";
import { formatNumber, cn } from "@/lib/utils";

export function ResourceCard({ source, onClick }: { source: SupplySource; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col gap-3 rounded-sm border border-border bg-surface p-4 text-left shadow-card transition-colors hover:border-primary/40 hover:bg-primary-tint/30"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-text">{source.name}</p>
          <p className="text-[11px] text-muted">{source.type} · {source.partnerOrg}</p>
        </div>
        <span
          className={cn(
            "flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-[11px] font-medium",
            source.verified ? "bg-primary-tint text-primary-dark" : "bg-surface-sunken text-muted",
          )}
        >
          {source.verified ? <ShieldCheck className="h-3 w-3" strokeWidth={2} /> : <ShieldAlert className="h-3 w-3" strokeWidth={2} />}
          {source.verified ? "Verified" : "Unverified"}
        </span>
      </div>

      <div className="flex flex-col gap-2">
        {source.inventory.map((line) => {
          const remaining = line.available - line.allocated;
          return (
            <div key={line.resource} className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-text">{line.resource}</span>
                <span className="text-muted tabular">
                  {formatNumber(remaining)} / {formatNumber(line.available)} {line.unit} remaining
                </span>
              </div>
              <div className="flex h-1.5 overflow-hidden rounded-full bg-surface-sunken">
                <div
                  className="h-full bg-accent"
                  style={{ width: `${(line.delivered / line.available) * 100}%` }}
                  title={`Delivered: ${line.delivered}`}
                />
                <div
                  className="h-full bg-primary"
                  style={{ width: `${((line.allocated - line.delivered) / line.available) * 100}%` }}
                  title={`Allocated: ${line.allocated - line.delivered}`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </button>
  );
}
