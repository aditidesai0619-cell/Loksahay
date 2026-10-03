import { useEffect, useState } from "react";
import type { Coordinator, OperationalSummary } from "@/types";
import { service, ApiError } from "@/data/service";
import { PageHeader } from "@/components/layout/PageHeader";
import { LoadingState, ErrorState } from "@/components/common/States";

export function CoordinatorProfile() {
  const [coordinator, setCoordinator] = useState<Coordinator | null>(null);
  const [summary, setSummary] = useState<OperationalSummary | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([service.getCoordinator(), service.getOperationalSummary()])
      .then(([c, s]) => {
        setCoordinator(c);
        setSummary(s);
      })
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend"));
  }, []);

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="Coordinator Profile" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load coordinator profile" description={loadError} />
        </div>
      </div>
    );
  }

  if (!coordinator || !summary) {
    return <LoadingState title="Loading coordinator profile…" className="h-full" />;
  }

  return (
    <div className="flex flex-col">
      <PageHeader title="Coordinator Profile" />

      <div className="flex flex-col gap-4 p-5 sm:p-6">
        <div className="flex items-center gap-4 rounded-sm border border-border bg-surface p-5 shadow-card">
          <div className="flex h-14 w-14 flex-none items-center justify-center rounded-full bg-primary-tint text-lg font-semibold text-primary-dark">
            {coordinator.initials}
          </div>
          <div>
            <p className="text-base font-semibold text-text">{coordinator.name}</p>
            <p className="text-sm text-secondary">{coordinator.role}</p>
            <p className="text-xs text-muted">Assigned region: {coordinator.region}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <InfoCard label="Critical Needs Tracked" value={summary.criticalNeeds} />
          <InfoCard label="Active Deliveries" value={summary.activeDeliveries} />
          <InfoCard label="Vehicles Available" value={summary.vehiclesAvailable} />
        </div>

        <div className="rounded-sm border border-border bg-surface p-4 shadow-card">
          <h2 className="mb-2 text-sm font-semibold text-text">Session</h2>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-[11px] text-muted">Role</dt>
              <dd className="font-medium text-text">Relief Coordinator</dd>
            </div>
            <div>
              <dt className="text-[11px] text-muted">Access Level</dt>
              <dd className="font-medium text-text">Full — allocation, replanning, scenario tools</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-sm border border-border bg-surface p-3.5 shadow-card">
      <p className="text-lg font-semibold tabular text-text">{value}</p>
      <p className="text-[11px] text-muted">{label}</p>
    </div>
  );
}
