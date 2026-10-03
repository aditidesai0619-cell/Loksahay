import { useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";
import type { AlgorithmSnapshot, OperationalSummary, RoadEdge, Vehicle } from "@/types";
import { service, ApiError } from "@/data/service";
import { formatDateTime } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { LoadingState, ErrorState } from "@/components/common/States";
import { Badge } from "@/components/common/Badge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Modal } from "@/components/common/Modal";
import { AlgorithmPanel } from "@/components/domain/AlgorithmPanel";

export function SystemStatus() {
  const [summary, setSummary] = useState<OperationalSummary | null>(null);
  const [snapshot, setSnapshot] = useState<AlgorithmSnapshot | null>(null);
  const [roadEdges, setRoadEdges] = useState<RoadEdge[] | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [confirmingReset, setConfirmingReset] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);
  const [resetDone, setResetDone] = useState(false);

  function load() {
    setLoadError(null);
    Promise.all([
      service.getOperationalSummary(),
      service.getAlgorithmSnapshot(),
      service.getRoadEdges(),
      service.getVehicles(),
    ])
      .then(([s, snap, edges, vs]) => {
        setSummary(s);
        setSnapshot(snap);
        setRoadEdges(edges);
        setVehicles(vs);
      })
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend"));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleResetDemo() {
    setResetting(true);
    setResetError(null);
    try {
      await service.resetDemo();
      setConfirmingReset(false);
      setResetDone(true);
      load();
    } catch (err) {
      setResetError(err instanceof ApiError ? err.message : "Could not reset the demo");
    } finally {
      setResetting(false);
    }
  }

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="System Status" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load system status" description={loadError} />
        </div>
      </div>
    );
  }

  if (!summary || !snapshot || !roadEdges || !vehicles) {
    return <LoadingState title="Checking system status…" className="h-full" />;
  }

  const blocked = roadEdges.filter((e) => e.condition === "Blocked").length;
  const degraded = roadEdges.filter((e) => e.condition === "Degraded").length;
  const unavailableVehicles = vehicles.filter((v) => v.status === "Unavailable").length;

  return (
    <div className="flex flex-col">
      <PageHeader
        title="System Status"
        subtitle="Operational health of the LokSahay coordination network"
        actions={
          <button
            onClick={() => {
              setResetDone(false);
              setResetError(null);
              setConfirmingReset(true);
            }}
            className="flex items-center gap-1.5 rounded-sm border border-border px-2.5 py-1.5 text-xs font-medium text-secondary hover:bg-surface-sunken"
          >
            <RotateCcw className="h-3.5 w-3.5" strokeWidth={1.75} />
            Reset Demo
          </button>
        }
      />

      <div className="flex flex-col gap-4 p-5 sm:p-6">
        {resetDone && (
          <div className="rounded-sm border border-primary/30 bg-primary-tint px-3.5 py-2 text-xs text-primary-dark">
            Demo reset — every request, source, vehicle, allocation, delivery and replan event is back to the
            deterministic seed state.
          </div>
        )}

        <div className="flex items-center justify-between rounded-sm border border-border bg-surface p-4 shadow-card">
          <div>
            <p className="text-sm font-semibold text-text">Overall System Status</p>
            <p className="text-[11px] text-muted">Last plan generated {formatDateTime(summary.lastPlanGeneratedAt)}</p>
          </div>
          <Badge tone={summary.systemStatus === "Operational" ? "primary" : "critical"} dot>
            {summary.systemStatus}
          </Badge>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <StatusRow label="Road Network" value={`${roadEdges.length - blocked - degraded} clear · ${degraded} degraded · ${blocked} blocked`} tone={blocked > 0 ? "warning" : "primary"} />
          <StatusRow label="Fleet Availability" value={`${vehicles.length - unavailableVehicles} of ${vehicles.length} vehicles operational`} tone={unavailableVehicles > 0 ? "warning" : "primary"} />
          <StatusRow label="Allocation Engine" value={`Running · ${snapshot.feasibleRoutes} feasible request↔source routes identified`} tone="primary" />
        </div>

        <AlgorithmPanel snapshot={snapshot} />

        <section>
          <h2 className="mb-2 text-sm font-semibold text-text">Road Segments</h2>
          <div className="overflow-hidden rounded-sm border border-border shadow-card">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-sunken text-[11px] uppercase text-muted">
                  <th className="px-3 py-2 text-left">Segment</th>
                  <th className="px-3 py-2 text-left">Distance</th>
                  <th className="px-3 py-2 text-left">Condition</th>
                </tr>
              </thead>
              <tbody>
                {roadEdges.map((e) => (
                  <tr key={e.id} className="border-b border-border last:border-0">
                    <td className="px-3 py-2 font-medium">{e.id} · {e.from} ↔ {e.to}</td>
                    <td className="px-3 py-2 tabular text-muted">{e.distanceKm} km</td>
                    <td className="px-3 py-2">
                      <StatusBadge kind="road" status={e.condition} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <Modal
        open={confirmingReset}
        onClose={() => !resetting && setConfirmingReset(false)}
        title="Reset Demo"
        description="This wipes every request, source, vehicle, allocation, delivery, tracking event and replan event, then reseeds the deterministic initial demo state. This cannot be undone."
        footer={
          <>
            <button
              onClick={() => setConfirmingReset(false)}
              disabled={resetting}
              className="rounded-sm border border-border px-3 py-1.5 text-xs font-medium text-secondary hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleResetDemo}
              disabled={resetting}
              className="rounded-sm bg-critical px-3 py-1.5 text-xs font-medium text-background hover:bg-critical/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {resetting ? "Resetting…" : "Reset Demo"}
            </button>
          </>
        }
      >
        {resetError && <p className="text-xs text-critical">{resetError}</p>}
      </Modal>
    </div>
  );
}

function StatusRow({ label, value, tone }: { label: string; value: string; tone: "primary" | "warning" }) {
  return (
    <div className="rounded-sm border border-border bg-surface p-3.5 shadow-card">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-text">{label}</p>
        <span className={tone === "primary" ? "h-1.5 w-1.5 rounded-full bg-primary" : "h-1.5 w-1.5 rounded-full bg-warning"} />
      </div>
      <p className="mt-1 text-[11px] text-muted">{value}</p>
    </div>
  );
}
