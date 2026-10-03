import { useEffect, useState } from "react";
import type { Allocation, AffectedRequest, SupplySource, Vehicle, Route } from "@/types";
import { service, ApiError } from "@/data/service";
import { PageHeader } from "@/components/layout/PageHeader";
import { LoadingState, EmptyState, ErrorState } from "@/components/common/States";
import { Modal } from "@/components/common/Modal";
import { AllocationRow } from "@/components/domain/AllocationRow";

interface WorkspaceData {
  allocations: Allocation[];
  requests: Map<string, AffectedRequest>;
  sources: Map<string, SupplySource>;
  vehicles: Map<string, Vehicle>;
  routes: Map<string, Route>;
}

export function AllocationWorkspace() {
  const [data, setData] = useState<WorkspaceData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [modifyTarget, setModifyTarget] = useState<Allocation | null>(null);
  const [modifyValue, setModifyValue] = useState<number>(0);
  const [modifySaving, setModifySaving] = useState(false);
  const [modifyError, setModifyError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function load() {
    setLoadError(null);
    try {
      const [allocations, requests, sources, vehicles, routes] = await Promise.all([
        service.getAllocations(),
        service.getAffectedRequests(),
        service.getSupplySources(),
        service.getVehicles(),
        service.getRoutes(),
      ]);
      setData({
        allocations,
        requests: new Map(requests.map((r) => [r.id, r])),
        sources: new Map(sources.map((s) => [s.id, s])),
        vehicles: new Map(vehicles.map((v) => [v.id, v])),
        routes: new Map(routes.map((r) => [r.id, r])),
      });
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
        <PageHeader title="Allocation Workspace" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load the allocation workspace" description={loadError} />
        </div>
      </div>
    );
  }

  if (!data) {
    return <LoadingState title="Loading allocation workspace…" className="h-full" />;
  }

  async function handleAccept(id: string) {
    setBusyId(id);
    setActionError(null);
    try {
      await service.decideAllocation(id, "Accepted");
      await load();
    } catch (err) {
      setActionError(err instanceof ApiError ? `${id}: ${err.message}` : `${id}: could not accept`);
    } finally {
      setBusyId(null);
    }
  }

  async function handleReject(id: string) {
    setBusyId(id);
    setActionError(null);
    try {
      await service.decideAllocation(id, "Rejected");
      await load();
    } catch (err) {
      setActionError(err instanceof ApiError ? `${id}: ${err.message}` : `${id}: could not reject`);
    } finally {
      setBusyId(null);
    }
  }

  function handleModifyOpen(id: string) {
    if (!data) return;
    const allocation = data.allocations.find((a) => a.id === id);
    if (allocation) {
      setModifyTarget(allocation);
      setModifyValue(allocation.quantity);
      setModifyError(null);
    }
  }

  async function handleModifyConfirm() {
    if (!modifyTarget) return;
    setModifySaving(true);
    setModifyError(null);
    try {
      await service.decideAllocation(modifyTarget.id, "Modified", modifyValue);
      setModifyTarget(null);
      await load();
    } catch (err) {
      setModifyError(err instanceof ApiError ? err.message : "Could not modify this allocation");
    } finally {
      setModifySaving(false);
    }
  }

  return (
    <div className="flex flex-col">
      <PageHeader
        title="Allocation Workspace"
        subtitle="Request → Source → Resource → Vehicle → Route → ETA → Deadline"
      />

      <div className="flex flex-col gap-3 p-5 sm:p-6">
        {actionError && (
          <div className="rounded-sm border border-critical/30 bg-critical-tint px-3.5 py-2 text-xs text-critical">
            {actionError}
          </div>
        )}
        {data.allocations.length === 0 ? (
          <EmptyState title="No allocations proposed" />
        ) : (
          data.allocations.map((allocation) => {
            const request = data.requests.get(allocation.requestId);
            const source = data.sources.get(allocation.sourceId);
            const vehicle = data.vehicles.get(allocation.vehicleId);
            const route = data.routes.get(allocation.routeId);
            if (!request || !source || !vehicle || !route) return null;
            return (
              <AllocationRow
                key={allocation.id}
                allocation={allocation}
                request={request}
                source={source}
                vehicle={vehicle}
                route={route}
                busy={busyId === allocation.id}
                onAccept={handleAccept}
                onModify={handleModifyOpen}
                onReject={handleReject}
              />
            );
          })
        )}
      </div>

      <Modal
        open={!!modifyTarget}
        onClose={() => setModifyTarget(null)}
        title={`Modify allocation ${modifyTarget?.id ?? ""}`}
        description="Adjust the allocated quantity. The route and vehicle assignment remain the same."
        footer={
          <>
            <button
              onClick={() => setModifyTarget(null)}
              disabled={modifySaving}
              className="rounded-sm border border-border px-3 py-1.5 text-xs font-medium text-secondary hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleModifyConfirm}
              disabled={modifySaving}
              className="rounded-sm bg-primary px-3 py-1.5 text-xs font-medium text-background hover:bg-primary-dark disabled:cursor-not-allowed disabled:opacity-50"
            >
              {modifySaving ? "Saving…" : "Confirm Modification"}
            </button>
          </>
        }
      >
        {modifyTarget && (
          <div className="flex flex-col gap-2">
            <label className="flex flex-col gap-1.5 text-xs text-secondary">
              Quantity ({modifyTarget.unit})
              <input
                type="number"
                min={0}
                value={modifyValue}
                onChange={(e) => setModifyValue(Number(e.target.value))}
                className="rounded-sm border border-border bg-surface px-2.5 py-1.5 text-sm text-text"
              />
            </label>
            {modifyError && <p className="text-xs text-critical">{modifyError}</p>}
          </div>
        )}
      </Modal>
    </div>
  );
}
