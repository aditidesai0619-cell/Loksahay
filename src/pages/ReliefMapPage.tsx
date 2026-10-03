import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import type { AffectedRequest, Delivery, RoadEdge, RoadNode, Route, SupplySource, Vehicle } from "@/types";
import { service, ApiError } from "@/data/service";
import { PageHeader } from "@/components/layout/PageHeader";
import { LoadingState, ErrorState } from "@/components/common/States";
import { Drawer } from "@/components/common/Drawer";
import { StatusBadge } from "@/components/common/StatusBadge";
import { PriorityBadge } from "@/components/common/PriorityBadge";
import { UnmetDemandPanel } from "@/components/domain/UnmetDemandPanel";
import { ReliefMap, DEFAULT_LAYER_STATE, type MapLayerState } from "@/components/map/ReliefMap";

interface MapData {
  requests: AffectedRequest[];
  sources: SupplySource[];
  vehicles: Vehicle[];
  routes: Route[];
  roadNodes: RoadNode[];
  roadEdges: RoadEdge[];
  deliveries: Delivery[];
}

type Selection =
  | { kind: "request"; data: AffectedRequest }
  | { kind: "source"; data: SupplySource }
  | { kind: "vehicle"; data: Vehicle }
  | { kind: "edge"; data: RoadEdge };

const LAYER_LABELS: { key: keyof MapLayerState; label: string }[] = [
  { key: "affectedAreas", label: "Affected Areas" },
  { key: "supplySources", label: "Supply Sources" },
  { key: "vehicles", label: "Vehicles" },
  { key: "routes", label: "Routes" },
  { key: "blockedRoads", label: "Road Network" },
];

export function ReliefMapPage() {
  const [data, setData] = useState<MapData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [layers, setLayers] = useState<MapLayerState>(DEFAULT_LAYER_STATE);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const [highlightedRouteId, setHighlightedRouteId] = useState<string | undefined>(
    searchParams.get("routeId") ?? undefined,
  );

  useEffect(() => {
    Promise.all([
      service.getAffectedRequests(),
      service.getSupplySources(),
      service.getVehicles(),
      service.getRoutes(),
      service.getRoadNodes(),
      service.getRoadEdges(),
      service.getDeliveries(),
    ])
      .then(([requests, sources, vehicles, routes, roadNodes, roadEdges, deliveries]) => {
        setData({ requests, sources, vehicles, routes, roadNodes, roadEdges, deliveries });
      })
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend"));
  }, []);

  // Arriving via "View on Map" (e.g. from Transport) with ?routeId=... also
  // opens that route's vehicle detail, so the full Source/Route/Vehicle/
  // Destination picture is visible, not just the highlighted line.
  const deliveryByRoute = useMemo(() => {
    const map = new Map<string, Delivery>();
    data?.deliveries.forEach((d) => map.set(d.routeId, d));
    return map;
  }, [data]);

  useEffect(() => {
    if (!data || !highlightedRouteId) return;
    const delivery = deliveryByRoute.get(highlightedRouteId);
    const vehicle = delivery ? data.vehicles.find((v) => v.id === delivery.vehicleId) : undefined;
    if (vehicle) setSelection({ kind: "vehicle", data: vehicle });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  function selectVehicle(v: Vehicle) {
    setSelection({ kind: "vehicle", data: v });
    const delivery = data?.deliveries.find((d) => d.vehicleId === v.id);
    setHighlightedRouteId(delivery?.routeId);
  }

  function clearSelection() {
    setSelection(null);
    setHighlightedRouteId(undefined);
    if (searchParams.has("routeId")) {
      searchParams.delete("routeId");
      setSearchParams(searchParams, { replace: true });
    }
  }

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="Relief Map" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load the relief map" description={loadError} />
        </div>
      </div>
    );
  }

  if (!data) {
    return <LoadingState title="Loading relief map…" className="h-full" />;
  }

  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Relief Map" subtitle="Affected areas, supply sources, vehicles, routes and road conditions" />

      <div className="flex flex-wrap items-center gap-1.5 border-b border-border bg-surface px-5 py-3 shadow-card sm:px-6">
        <span className="mr-1 text-[11px] font-semibold uppercase tracking-wide text-muted">Layers</span>
        {LAYER_LABELS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setLayers((prev) => ({ ...prev, [key]: !prev[key] }))}
            className={
              layers[key]
                ? "rounded-sm border border-primary/30 bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary-dark"
                : "rounded-sm border border-border bg-surface px-2.5 py-1 text-xs font-medium text-muted"
            }
          >
            {label}
          </button>
        ))}
        {highlightedRouteId && (
          <button
            onClick={clearSelection}
            className="ml-auto rounded-sm border border-primary/30 bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary-dark"
          >
            Clear route highlight ({highlightedRouteId})
          </button>
        )}
      </div>

      <div className="relative flex-1 border-b border-border">
        <div className="pointer-events-none absolute left-3 top-3 z-5 rounded-sm border border-border bg-surface/95 px-3 py-2 text-[11px] text-muted shadow-card">
          <p className="font-semibold uppercase tracking-wide text-muted">Legend</p>
          <div className="mt-1.5 flex flex-col gap-1">
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-critical" /> Critical need / blocked road</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-warning" /> High urgency / degraded road</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-primary" /> Verified source / vehicle</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rotate-45 bg-secondary" /> Unverified source</span>
          </div>
        </div>
        <ReliefMap
          requests={data.requests}
          sources={data.sources}
          vehicles={data.vehicles}
          routes={data.routes}
          roadNodes={data.roadNodes}
          roadEdges={data.roadEdges}
          deliveries={data.deliveries}
          layers={layers}
          highlightedRouteId={highlightedRouteId}
          heightClassName="h-full"
          onSelectRequest={(r) => setSelection({ kind: "request", data: r })}
          onSelectSource={(s) => setSelection({ kind: "source", data: s })}
          onSelectVehicle={selectVehicle}
          onSelectEdge={(e) => setSelection({ kind: "edge", data: e })}
        />
      </div>

      <Drawer open={!!selection} onClose={clearSelection} title={selectionTitle(selection)} subtitle={selectionSubtitle(selection)}>
        {selection?.kind === "request" && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <PriorityBadge level={selection.data.urgency} />
              <StatusBadge kind="request" status={selection.data.status} />
            </div>
            <UnmetDemandPanel request={selection.data} />
          </div>
        )}
        {selection?.kind === "source" && (
          <div className="flex flex-col gap-2 text-sm">
            {selection.data.inventory.map((line) => (
              <div key={line.resource} className="flex justify-between border-b border-border pb-1.5 last:border-0">
                <span>{line.resource}</span>
                <span className="tabular text-muted">
                  {line.available - line.allocated} / {line.available} {line.unit} remaining
                </span>
              </div>
            ))}
          </div>
        )}
        {selection?.kind === "vehicle" && (
          <div className="flex flex-col gap-2 text-sm">
            <StatusBadge kind="vehicle" status={selection.data.status} />
            <p className="text-xs text-muted">Capacity: {selection.data.capacityKg} kg</p>
            {selection.data.cargo.map((c) => (
              <p key={c.resource} className="text-xs text-secondary">
                Cargo: {c.quantity} {c.unit} {c.resource}
              </p>
            ))}
            {(() => {
              const delivery = data.deliveries.find((d) => d.vehicleId === selection.data.id);
              if (!delivery) return null;
              return (
                <div className="mt-1 border-t border-border pt-2 text-xs text-muted">
                  {delivery.originName} → {delivery.destinationName} · route highlighted on map
                </div>
              );
            })()}
          </div>
        )}
        {selection?.kind === "edge" && (
          <div className="flex flex-col gap-2 text-sm">
            <StatusBadge kind="road" status={selection.data.condition} />
            <p className="text-xs text-muted">Distance: {selection.data.distanceKm} km</p>
            {selection.data.blockedReason && <p className="text-xs text-critical">{selection.data.blockedReason}</p>}
          </div>
        )}
      </Drawer>
    </div>
  );
}

function selectionTitle(selection: Selection | null): string {
  if (!selection) return "";
  switch (selection.kind) {
    case "request":
      return selection.data.areaName;
    case "source":
      return selection.data.name;
    case "vehicle":
      return selection.data.id;
    case "edge":
      return `${selection.data.id} · ${selection.data.from} ↔ ${selection.data.to}`;
  }
}

function selectionSubtitle(selection: Selection | null): string | undefined {
  if (!selection) return undefined;
  switch (selection.kind) {
    case "request":
      return `${selection.data.id} · ${selection.data.resource}`;
    case "source":
      return `${selection.data.type} · ${selection.data.partnerOrg}`;
    case "vehicle":
      return `${selection.data.partner} · ${selection.data.type}`;
    case "edge":
      return "Road segment";
  }
}
