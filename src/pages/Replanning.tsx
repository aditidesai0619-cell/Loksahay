import { useEffect, useState } from "react";
import { TriangleAlert, CircleCheck } from "lucide-react";
import type { ReplanEvent } from "@/types";
import { service, ApiError } from "@/data/service";
import { formatNumber, formatTime } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { LoadingState, EmptyState, ErrorState } from "@/components/common/States";
import { Badge } from "@/components/common/Badge";
import { Modal } from "@/components/common/Modal";
import { ReplanningComparison } from "@/components/domain/ReplanningComparison";

export function Replanning() {
  const [events, setEvents] = useState<ReplanEvent[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [alternativesFor, setAlternativesFor] = useState<ReplanEvent | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function load() {
    setLoadError(null);
    try {
      setEvents(await service.getReplanEvents());
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend");
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="Replanning Center" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load the replanning center" description={loadError} />
        </div>
      </div>
    );
  }

  if (!events) {
    return <LoadingState title="Checking network for changes…" className="h-full" />;
  }

  async function handleApply(id: string) {
    setBusyId(id);
    setActionError(null);
    try {
      await service.applyReplan(id);
      await load();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not apply this replan");
    } finally {
      setBusyId(null);
    }
  }

  async function handleDismiss(id: string) {
    setBusyId(id);
    setActionError(null);
    try {
      await service.dismissReplan(id);
      await load();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not dismiss this replan");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="flex flex-col">
      <PageHeader title="Replanning Center" subtitle="Dynamic re-optimization triggered by network changes" />

      <div className="flex flex-col gap-4 p-5 sm:p-6">
        {actionError && (
          <div className="rounded-sm border border-critical/30 bg-critical-tint px-3.5 py-2 text-xs text-critical">
            {actionError}
          </div>
        )}
        {events.length === 0 ? (
          <EmptyState title="No network changes detected" description="All current allocations remain feasible." />
        ) : (
          events.map((event) => {
            const busy = busyId === event.id;
            return (
              <div key={event.id} className="flex flex-col gap-4 rounded-sm border border-border bg-surface p-4 shadow-card">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5">
                    <TriangleAlert className="mt-0.5 h-4.5 w-4.5 flex-none text-critical" strokeWidth={1.75} />
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-critical">Network Change Detected</p>
                      <p className="mt-0.5 text-sm text-text">{event.triggerDescription}</p>
                      <p className="mt-0.5 text-[11px] text-muted">Detected at {formatTime(event.triggeredAt)}</p>
                    </div>
                  </div>
                  <Badge tone={event.status === "Applied" ? "primary" : event.status === "Dismissed" ? "muted" : "warning"}>
                    {event.status}
                  </Badge>
                </div>

                <div className="grid grid-cols-3 gap-3 rounded-sm border border-border bg-surface-sunken p-3 text-center">
                  <StatBlock label="Affected Deliveries" value={event.affectedDeliveryIds.length} />
                  <StatBlock label="Vehicles Affected" value={event.vehiclesAffectedCount} />
                  <StatBlock label="Deadlines at Risk" value={event.deadlinesAtRiskCount} />
                </div>

                <ReplanningComparison oldPlan={event.oldPlan} newPlan={event.newPlan} />

                {event.metricsBefore && event.metricsAfter && (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[480px] text-xs">
                      <thead>
                        <tr className="border-b border-border text-[10px] uppercase text-muted">
                          <th className="px-2 py-1.5 text-left">Network-wide Impact</th>
                          <th className="px-2 py-1.5 text-right">Before</th>
                          <th className="px-2 py-1.5 text-right">After</th>
                        </tr>
                      </thead>
                      <tbody>
                        <ImpactRow label="Demand Fulfilled %" before={event.metricsBefore.demandFulfilledPct} after={event.metricsAfter.demandFulfilledPct} suffix="%" />
                        <ImpactRow label="On-Time Delivery %" before={event.metricsBefore.onTimeDeliveryPct} after={event.metricsAfter.onTimeDeliveryPct} suffix="%" />
                        <ImpactRow label="Unmet Demand (units)" before={event.metricsBefore.unmetDemandUnits} after={event.metricsAfter.unmetDemandUnits} inverse />
                      </tbody>
                    </table>
                  </div>
                )}

                {event.status === "Pending" && (
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setAlternativesFor(event)}
                      disabled={busy}
                      className="rounded-sm border border-border px-3 py-1.5 text-xs font-medium text-secondary hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      View Alternatives
                    </button>
                    <button
                      onClick={() => handleApply(event.id)}
                      disabled={busy}
                      className="rounded-sm bg-primary px-3 py-1.5 text-xs font-medium text-background hover:bg-primary-dark disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {busy ? "Applying…" : "Apply New Plan"}
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <Modal
        open={!!alternativesFor}
        onClose={() => setAlternativesFor(null)}
        title="Alternatives considered"
        description={alternativesFor?.triggerDescription}
        footer={
          <>
            <button
              onClick={async () => {
                if (!alternativesFor) return;
                const id = alternativesFor.id;
                setAlternativesFor(null);
                await handleDismiss(id);
              }}
              className="rounded-sm border border-border px-3 py-1.5 text-xs font-medium text-secondary hover:bg-surface-sunken"
            >
              Dismiss This Replan
            </button>
            <button
              onClick={async () => {
                if (!alternativesFor) return;
                const id = alternativesFor.id;
                setAlternativesFor(null);
                await handleApply(id);
              }}
              className="rounded-sm bg-primary px-3 py-1.5 text-xs font-medium text-background hover:bg-primary-dark"
            >
              Apply New Plan
            </button>
          </>
        }
      >
        <ul className="flex flex-col gap-2">
          {alternativesFor?.alternativesConsidered.map((alt, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-secondary">
              <CircleCheck className="mt-0.5 h-3.5 w-3.5 flex-none text-primary" strokeWidth={1.75} />
              <span>{alt}</span>
            </li>
          ))}
        </ul>
      </Modal>
    </div>
  );
}

function StatBlock({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="text-lg font-semibold tabular text-text">{value}</p>
      <p className="text-[10px] uppercase tracking-wide text-muted">{label}</p>
    </div>
  );
}

function ImpactRow({
  label,
  before,
  after,
  suffix = "",
  inverse = false,
}: {
  label: string;
  before: number;
  after: number;
  suffix?: string;
  inverse?: boolean;
}) {
  const improved = inverse ? after < before : after > before;
  const changed = after !== before;
  return (
    <tr className="border-b border-border last:border-0">
      <td className="px-2 py-1.5 text-text">{label}</td>
      <td className="px-2 py-1.5 text-right tabular text-muted">{formatNumber(before)}{suffix}</td>
      <td className={`px-2 py-1.5 text-right tabular font-medium ${changed ? (improved ? "text-primary" : "text-critical") : "text-text"}`}>
        {formatNumber(after)}{suffix}
      </td>
    </tr>
  );
}
