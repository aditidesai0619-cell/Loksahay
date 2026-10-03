import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { AffectedRequest, RequestStatus, ResourceType, UrgencyLevel } from "@/types";
import { service, ApiError } from "@/data/service";
import { formatNumber } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { DataTable, type DataTableColumn } from "@/components/common/DataTable";
import { StatusBadge } from "@/components/common/StatusBadge";
import { PriorityBadge } from "@/components/common/PriorityBadge";
import { DeadlineIndicator } from "@/components/common/DeadlineIndicator";
import { LoadingState, ErrorState } from "@/components/common/States";
import { Drawer } from "@/components/common/Drawer";
import { UnmetDemandPanel } from "@/components/domain/UnmetDemandPanel";

const RESOURCE_OPTIONS: ResourceType[] = ["Food", "Medicine", "Water", "Essentials"];
const URGENCY_OPTIONS: UrgencyLevel[] = ["Critical", "High", "Medium", "Low"];
const STATUS_OPTIONS: RequestStatus[] = ["Unfulfilled", "Partial", "Fulfilled"];

export function Needs() {
  const [requests, setRequests] = useState<AffectedRequest[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AffectedRequest | null>(null);
  const [resourceFilter, setResourceFilter] = useState<ResourceType | "All">("All");
  const [urgencyFilter, setUrgencyFilter] = useState<UrgencyLevel | "All">("All");
  const [statusFilter, setStatusFilter] = useState<RequestStatus | "All">("All");
  const [areaFilter, setAreaFilter] = useState<string>("All");

  useEffect(() => {
    service
      .getAffectedRequests()
      .then(setRequests)
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend"));
  }, []);

  const areaOptions = useMemo(() => {
    if (!requests) return [];
    return Array.from(new Set(requests.map((r) => r.areaName))).sort();
  }, [requests]);

  const filtered = useMemo(() => {
    if (!requests) return [];
    return requests.filter(
      (r) =>
        (resourceFilter === "All" || r.resource === resourceFilter) &&
        (urgencyFilter === "All" || r.urgency === urgencyFilter) &&
        (statusFilter === "All" || r.status === statusFilter) &&
        (areaFilter === "All" || r.areaName === areaFilter),
    );
  }, [requests, resourceFilter, urgencyFilter, statusFilter, areaFilter]);

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="Needs" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load affected requests" description={loadError} />
        </div>
      </div>
    );
  }

  if (!requests) {
    return <LoadingState title="Loading affected requests…" className="h-full" />;
  }

  const columns: DataTableColumn<AffectedRequest>[] = [
    { key: "id", header: "Request ID", render: (r) => <span className="font-medium">{r.id}</span> },
    { key: "area", header: "Area", render: (r) => r.areaName },
    { key: "resource", header: "Resource", render: (r) => r.resource },
    { key: "required", header: "Required", align: "right", render: (r) => `${formatNumber(r.required)} ${r.unit}` },
    { key: "allocated", header: "Allocated", align: "right", render: (r) => `${formatNumber(r.allocated)} ${r.unit}` },
    {
      key: "unmet",
      header: "Unmet",
      align: "right",
      render: (r) => {
        const unmet = r.required - r.allocated;
        return <span className={unmet > 0 ? "font-medium text-critical" : "text-primary"}>{formatNumber(unmet)} {r.unit}</span>;
      },
    },
    { key: "people", header: "People Affected", align: "right", render: (r) => formatNumber(r.peopleAffected) },
    { key: "urgency", header: "Urgency", render: (r) => <PriorityBadge level={r.urgency} /> },
    { key: "deadline", header: "Deadline", render: (r) => <DeadlineIndicator deadlineIso={r.deadline} /> },
    { key: "status", header: "Status", render: (r) => <StatusBadge kind="request" status={r.status} /> },
  ];

  return (
    <div className="flex flex-col">
      <PageHeader title="Needs" subtitle={`${filtered.length} of ${requests.length} affected requests`} />

      <div className="flex flex-wrap gap-2.5 border-b border-border bg-surface px-5 py-3 shadow-card sm:px-6">
        <FilterSelect label="Resource" value={resourceFilter} onChange={setResourceFilter} options={RESOURCE_OPTIONS} />
        <FilterSelect label="Urgency" value={urgencyFilter} onChange={setUrgencyFilter} options={URGENCY_OPTIONS} />
        <FilterSelect label="Status" value={statusFilter} onChange={setStatusFilter} options={STATUS_OPTIONS} />
        <FilterSelect label="Area" value={areaFilter} onChange={setAreaFilter} options={areaOptions} />
      </div>

      <div className="p-5 sm:p-6">
        <DataTable columns={columns} rows={filtered} rowKey={(r) => r.id} onRowClick={setSelected} />
      </div>

      <Drawer
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `${selected.id} · ${selected.areaName}` : ""}
        subtitle={selected ? `${selected.resource} · ${selected.location.lat.toFixed(3)}, ${selected.location.lng.toFixed(3)}` : undefined}
      >
        {selected && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <PriorityBadge level={selected.urgency} />
              <StatusBadge kind="request" status={selected.status} />
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <Detail label="People Affected" value={formatNumber(selected.peopleAffected)} />
              <Detail label="Required" value={`${formatNumber(selected.required)} ${selected.unit}`} />
              <Detail label="Allocated" value={`${formatNumber(selected.allocated)} ${selected.unit}`} />
              <Detail label="Deadline">
                <DeadlineIndicator deadlineIso={selected.deadline} />
              </Detail>
            </dl>
            <UnmetDemandPanel request={selected} />
          </div>
        )}
      </Drawer>
    </div>
  );
}

function FilterSelect<T extends string>({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: T | "All";
  onChange: (v: T | "All") => void;
  options: T[];
}) {
  return (
    <label className="flex items-center gap-1.5 text-xs text-secondary">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T | "All")}
        className="rounded-sm border border-border bg-surface px-2 py-1.5 text-xs font-medium text-text"
      >
        <option value="All">All</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

function Detail({ label, value, children }: { label: string; value?: string; children?: ReactNode }) {
  return (
    <div>
      <dt className="text-[11px] text-muted">{label}</dt>
      <dd className="font-medium text-text">{children ?? value}</dd>
    </div>
  );
}
