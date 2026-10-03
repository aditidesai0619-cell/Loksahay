import { useEffect, useMemo, useState } from "react";
import { ShieldCheck, ShieldAlert } from "lucide-react";
import type { ResourceType, SupplySource } from "@/types";
import { service, ApiError } from "@/data/service";
import { formatNumber } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { LoadingState, ErrorState } from "@/components/common/States";
import { Drawer } from "@/components/common/Drawer";
import { ResourceCard } from "@/components/domain/ResourceCard";

const RESOURCE_OPTIONS: ResourceType[] = ["Food", "Medicine", "Water", "Essentials"];

export function Resources() {
  const [sources, setSources] = useState<SupplySource[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selected, setSelected] = useState<SupplySource | null>(null);
  const [resourceFilter, setResourceFilter] = useState<ResourceType | "All">("All");

  useEffect(() => {
    service
      .getSupplySources()
      .then(setSources)
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend"));
  }, []);

  const filtered = useMemo(() => {
    if (!sources) return [];
    if (resourceFilter === "All") return sources;
    return sources.filter((s) => s.inventory.some((i) => i.resource === resourceFilter));
  }, [sources, resourceFilter]);

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="Resources" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load the resource network" description={loadError} />
        </div>
      </div>
    );
  }

  if (!sources) {
    return <LoadingState title="Loading resource network…" className="h-full" />;
  }

  return (
    <div className="flex flex-col">
      <PageHeader title="Resources" subtitle={`${filtered.length} of ${sources.length} supply sources`} />

      <div className="flex flex-wrap gap-2.5 border-b border-border bg-surface px-5 py-3 shadow-card sm:px-6">
        <label className="flex items-center gap-1.5 text-xs text-secondary">
          Resource
          <select
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value as ResourceType | "All")}
            className="rounded-sm border border-border bg-surface px-2 py-1.5 text-xs font-medium text-text"
          >
            <option value="All">All</option>
            {RESOURCE_OPTIONS.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid grid-cols-1 gap-3 p-5 sm:grid-cols-2 sm:p-6 lg:grid-cols-3">
        {filtered.map((source) => (
          <ResourceCard key={source.id} source={source} onClick={() => setSelected(source)} />
        ))}
      </div>

      <Drawer
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected?.name ?? ""}
        subtitle={selected ? `${selected.type} · ${selected.partnerOrg}` : undefined}
      >
        {selected && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <span
                className={
                  selected.verified
                    ? "flex items-center gap-1 rounded-sm bg-primary-tint px-2 py-0.5 text-xs font-medium text-primary-dark"
                    : "flex items-center gap-1 rounded-sm bg-surface-sunken px-2 py-0.5 text-xs font-medium text-muted"
                }
              >
                {selected.verified ? <ShieldCheck className="h-3.5 w-3.5" /> : <ShieldAlert className="h-3.5 w-3.5" />}
                {selected.verified ? "Verified source" : "Unverified source"}
              </span>
            </div>
            <p className="text-xs text-muted">
              Location: {selected.location.lat.toFixed(3)}, {selected.location.lng.toFixed(3)}
            </p>
            <div className="overflow-hidden rounded-sm border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-surface-sunken text-[11px] uppercase text-muted">
                    <th className="px-3 py-2 text-left">Resource</th>
                    <th className="px-3 py-2 text-right">Available</th>
                    <th className="px-3 py-2 text-right">Allocated</th>
                    <th className="px-3 py-2 text-right">Delivered</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.inventory.map((line) => (
                    <tr key={line.resource} className="border-b border-border last:border-0">
                      <td className="px-3 py-2 font-medium">{line.resource}</td>
                      <td className="px-3 py-2 text-right tabular">{formatNumber(line.available)} {line.unit}</td>
                      <td className="px-3 py-2 text-right tabular">{formatNumber(line.allocated)} {line.unit}</td>
                      <td className="px-3 py-2 text-right tabular">{formatNumber(line.delivered)} {line.unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
