import { Users } from "lucide-react";
import type { AffectedRequest } from "@/types";
import { formatNumber } from "@/lib/utils";
import { PriorityBadge } from "@/components/common/PriorityBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { DeadlineIndicator } from "@/components/common/DeadlineIndicator";

export function RequestCard({ request, onClick }: { request: AffectedRequest; onClick?: () => void }) {
  const unmet = request.required - request.allocated;

  return (
    <button
      onClick={onClick}
      className="flex w-full flex-col gap-3 rounded-sm border border-border bg-surface p-4 text-left shadow-card transition-colors hover:border-primary/40 hover:bg-primary-tint/30"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-text">{request.areaName}</p>
          <p className="text-[11px] text-muted">{request.id} · {request.resource}</p>
        </div>
        <PriorityBadge level={request.urgency} />
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <p className="text-[10px] uppercase text-muted">Required</p>
          <p className="font-semibold tabular text-text">{formatNumber(request.required)}</p>
        </div>
        <div>
          <p className="text-[10px] uppercase text-muted">Allocated</p>
          <p className="font-semibold tabular text-text">{formatNumber(request.allocated)}</p>
        </div>
        <div>
          <p className="text-[10px] uppercase text-muted">Unmet</p>
          <p className={unmet > 0 ? "font-semibold tabular text-critical" : "font-semibold tabular text-primary"}>
            {formatNumber(unmet)}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-border pt-2.5">
        <div className="flex items-center gap-1.5 text-[11px] text-muted">
          <Users className="h-3.5 w-3.5" strokeWidth={1.75} />
          {formatNumber(request.peopleAffected)} affected
        </div>
        <StatusBadge kind="request" status={request.status} />
      </div>

      <DeadlineIndicator deadlineIso={request.deadline} />
    </button>
  );
}
