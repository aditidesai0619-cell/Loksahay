import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, ChevronDown, ChevronUp, Map as MapIcon } from "lucide-react";
import type { Allocation, AffectedRequest, SupplySource, Vehicle, Route } from "@/types";
import { formatTime, cn } from "@/lib/utils";
import { StatusBadge } from "@/components/common/StatusBadge";
import { PriorityBadge } from "@/components/common/PriorityBadge";
import { DeadlineIndicator } from "@/components/common/DeadlineIndicator";
import { WhyAllocationPanel } from "./WhyAllocationPanel";

interface AllocationRowProps {
  allocation: Allocation;
  request: AffectedRequest;
  source: SupplySource;
  vehicle: Vehicle;
  route: Route;
  busy?: boolean;
  onAccept: (id: string) => void;
  onModify: (id: string) => void;
  onReject: (id: string) => void;
}

function FlowStep({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wide text-muted">{label}</span>
      <span className="text-sm font-medium text-text">{value}</span>
    </div>
  );
}

export function AllocationRow({ allocation, request, source, vehicle, route, busy = false, onAccept, onModify, onReject }: AllocationRowProps) {
  const [showWhy, setShowWhy] = useState(false);
  const disabled = allocation.status === "Rejected" || busy;

  return (
    <div className="rounded-sm border border-border bg-surface shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-3 p-4">
        <div className="flex flex-1 flex-wrap items-center gap-2.5">
          <FlowStep label="Request" value={`${request.id} · ${request.areaName}`} />
          <ArrowRight className="mt-4 h-3.5 w-3.5 flex-none text-muted" strokeWidth={1.75} />
          <FlowStep label="Source" value={source.name} />
          <ArrowRight className="mt-4 h-3.5 w-3.5 flex-none text-muted" strokeWidth={1.75} />
          <FlowStep label="Resource" value={`${allocation.quantity} ${allocation.unit} ${allocation.resource}`} />
          <ArrowRight className="mt-4 h-3.5 w-3.5 flex-none text-muted" strokeWidth={1.75} />
          <FlowStep label="Vehicle" value={`${vehicle.id} · ${vehicle.type}`} />
          <ArrowRight className="mt-4 h-3.5 w-3.5 flex-none text-muted" strokeWidth={1.75} />
          <FlowStep label="Route" value={route.edgeIds.join("-")} />
          <ArrowRight className="mt-4 h-3.5 w-3.5 flex-none text-muted" strokeWidth={1.75} />
          <FlowStep label="ETA" value={formatTime(allocation.etaIso)} />
          <ArrowRight className="mt-4 h-3.5 w-3.5 flex-none text-muted" strokeWidth={1.75} />
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wide text-muted">Deadline</span>
            <DeadlineIndicator deadlineIso={allocation.deadlineIso} etaIso={allocation.etaIso} atRisk={!allocation.meetsDeadline} />
          </div>
        </div>

        <div className="flex flex-none items-center gap-2">
          <span className="rounded-sm bg-primary-tint px-2 py-0.5 text-xs font-semibold tabular text-primary-dark" title="Priority score (prototype configurable priority model)">
            P {allocation.priorityScore.toFixed(2)}
          </span>
          <PriorityBadge level={request.urgency} />
          <StatusBadge kind="allocation" status={allocation.status} />
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-4 py-2.5">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowWhy((v) => !v)}
            className="flex items-center gap-1 text-xs font-medium text-primary hover:text-primary-dark"
          >
            Why this allocation?
            {showWhy ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
          <Link
            to={`/map?routeId=${allocation.routeId}`}
            className="flex items-center gap-1 text-xs font-medium text-secondary hover:text-text"
          >
            <MapIcon className="h-3.5 w-3.5" strokeWidth={1.75} />
            View on Map
          </Link>
        </div>

        <div className="flex items-center gap-2">
          <button
            disabled={disabled}
            onClick={() => onReject(allocation.id)}
            className={cn(
              "rounded-sm border border-border px-2.5 py-1 text-xs font-medium text-secondary hover:bg-surface-sunken",
              disabled && "cursor-not-allowed opacity-50",
            )}
          >
            Reject
          </button>
          <button
            disabled={disabled}
            onClick={() => onModify(allocation.id)}
            className={cn(
              "rounded-sm border border-accent/40 bg-accent-tint px-2.5 py-1 text-xs font-medium text-accent-dark hover:bg-accent-tint/70",
              disabled && "cursor-not-allowed opacity-50",
            )}
          >
            Modify
          </button>
          <button
            disabled={disabled}
            onClick={() => onAccept(allocation.id)}
            className={cn(
              "rounded-sm bg-primary px-2.5 py-1 text-xs font-medium text-background hover:bg-primary-dark",
              disabled && "cursor-not-allowed opacity-50",
            )}
          >
            {busy ? "Working…" : "Accept"}
          </button>
        </div>
      </div>

      {showWhy && (
        <div className="border-t border-border p-4 pt-3.5">
          <WhyAllocationPanel allocation={allocation} />
        </div>
      )}
    </div>
  );
}
