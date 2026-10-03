import type { AffectedRequest } from "@/types";
import { formatNumber, formatTime } from "@/lib/utils";
import { DeadlineIndicator } from "@/components/common/DeadlineIndicator";

export function UnmetDemandPanel({ request }: { request: AffectedRequest }) {
  const unmet = request.required - request.allocated;
  if (unmet <= 0) return null;

  return (
    <div className="rounded-sm border border-critical/25 bg-critical-tint/40 p-3.5">
      <p className="mb-2.5 text-xs font-semibold text-critical">Unmet Demand</p>
      <dl className="grid grid-cols-3 gap-2.5 text-xs">
        <div>
          <dt className="text-[10px] uppercase text-muted">Required</dt>
          <dd className="font-semibold tabular text-text">{formatNumber(request.required)} {request.unit}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase text-muted">Allocated</dt>
          <dd className="font-semibold tabular text-text">{formatNumber(request.allocated)} {request.unit}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase text-muted">Unmet</dt>
          <dd className="font-semibold tabular text-critical">{formatNumber(unmet)} {request.unit}</dd>
        </div>
      </dl>

      <div className="mt-3 flex flex-col gap-2 border-t border-critical/20 pt-3 text-xs">
        <div className="flex justify-between gap-3">
          <span className="text-muted">Reason</span>
          <span className="text-right font-medium text-text">{request.reason ?? "—"}</span>
        </div>
        <div className="flex justify-between gap-3">
          <span className="text-muted">Alternative Source</span>
          <span className="text-right font-medium text-text">{request.alternativeSourceName ?? "None identified"}</span>
        </div>
        {request.alternativeEtaIso && (
          <div className="flex justify-between gap-3">
            <span className="text-muted">Alternative ETA</span>
            <span className="text-right font-medium text-text tabular">{formatTime(request.alternativeEtaIso)}</span>
          </div>
        )}
        <div className="flex items-center justify-between gap-3">
          <span className="text-muted">Deadline</span>
          <DeadlineIndicator deadlineIso={request.deadline} />
        </div>
      </div>
    </div>
  );
}
