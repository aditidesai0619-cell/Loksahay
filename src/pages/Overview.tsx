import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Truck, PieChart, CarFront, Clock3 } from "lucide-react";
import type {
  AffectedRequest,
  AlgorithmSnapshot,
  Bottleneck,
  Delivery,
  OperationalSummary,
  RoadEdge,
  RoadNode,
  Route,
  SupplySource,
  Vehicle,
} from "@/types";
import { service, ApiError } from "@/data/service";
import { URGENCY_ORDER, formatDateTime, formatNumber, formatTime } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { MetricCard } from "@/components/common/MetricCard";
import { DataTable, type DataTableColumn } from "@/components/common/DataTable";
import { StatusBadge } from "@/components/common/StatusBadge";
import { PriorityBadge } from "@/components/common/PriorityBadge";
import { DeadlineIndicator } from "@/components/common/DeadlineIndicator";
import { LoadingState, ErrorState } from "@/components/common/States";
import { AlgorithmPanel } from "@/components/domain/AlgorithmPanel";
import { BottleneckPanel } from "@/components/domain/BottleneckPanel";
import { UnmetDemandPanel } from "@/components/domain/UnmetDemandPanel";
import { DeliveryTimeWatch } from "@/components/domain/DeliveryTimeWatch";
import { Drawer } from "@/components/common/Drawer";
import { Timeline } from "@/components/common/Timeline";
import { ReliefMap, DEFAULT_LAYER_STATE } from "@/components/map/ReliefMap";

interface OverviewData {
  summary: OperationalSummary;
  snapshot: AlgorithmSnapshot;
  requests: AffectedRequest[];
  deliveries: Delivery[];
  sources: SupplySource[];
  vehicles: Vehicle[];
  roadNodes: RoadNode[];
  roadEdges: RoadEdge[];
  routes: Route[];
  bottlenecks: Bottleneck[];
}

export function Overview() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedRequest, setSelectedRequest] = useState<AffectedRequest | null>(null);
  const [selectedDelivery, setSelectedDelivery] = useState<Delivery | null>(null);

  useEffect(() => {
    Promise.all([
      service.getOperationalSummary(),
      service.getAlgorithmSnapshot(),
      service.getAffectedRequests(),
      service.getDeliveries(),
      service.getSupplySources(),
      service.getVehicles(),
      service.getRoadNodes(),
      service.getRoadEdges(),
      service.getRoutes(),
      service.getBottlenecks(),
    ])
      .then(([summary, snapshot, requests, deliveries, sources, vehicles, roadNodes, roadEdges, routes, bottlenecks]) => {
        setData({ summary, snapshot, requests, deliveries, sources, vehicles, roadNodes, roadEdges, routes, bottlenecks });
      })
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend"));
  }, []);

  const criticalNeeds = useMemo(() => {
    if (!data) return [];
    return [...data.requests]
      .filter((r) => r.status !== "Fulfilled")
      .sort(
        (a, b) =>
          URGENCY_ORDER.indexOf(a.urgency) - URGENCY_ORDER.indexOf(b.urgency) ||
          b.required - b.allocated - (a.required - a.allocated),
      )
      .slice(0, 6);
  }, [data]);

  const activeDeliveries = useMemo(() => {
    if (!data) return [];
    return data.deliveries.filter((d) => d.status !== "Delivered");
  }, [data]);

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="Relief Operations" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load the relief operations overview" description={loadError} />
        </div>
      </div>
    );
  }

  if (!data) {
    return <LoadingState title="Loading relief operations overview…" className="h-full" />;
  }

  const needsColumns: DataTableColumn<AffectedRequest>[] = [
    { key: "area", header: "Area", render: (r) => <span className="font-medium">{r.areaName}</span> },
    { key: "resource", header: "Resource", render: (r) => r.resource },
    { key: "required", header: "Required", align: "right", render: (r) => formatNumber(r.required) },
    { key: "allocated", header: "Allocated", align: "right", render: (r) => formatNumber(r.allocated) },
    { key: "urgency", header: "Urgency", render: (r) => <PriorityBadge level={r.urgency} /> },
    { key: "deadline", header: "Deadline", render: (r) => <DeadlineIndicator deadlineIso={r.deadline} /> },
  ];

  const deliveryColumns: DataTableColumn<Delivery>[] = [
    { key: "id", header: "Delivery", render: (d) => <span className="font-medium">{d.id}</span> },
    { key: "vehicle", header: "Vehicle", render: (d) => d.vehicleId },
    { key: "destination", header: "Destination", render: (d) => d.destinationName },
    { key: "eta", header: "ETA", render: (d) => formatTime(d.etaIso) },
    {
      key: "deadline",
      header: "Deadline",
      render: (d) => <DeadlineIndicator deadlineIso={d.deadlineIso} etaIso={d.etaIso} atRisk={!d.meetsDeadline} />,
    },
    { key: "status", header: "Status", render: (d) => <StatusBadge kind="delivery" status={d.status} /> },
  ];

  return (
    <div className="flex flex-col">
      <PageHeader
        title="Relief Operations"
        subtitle={`Region: ${data.summary.region} · System Status: ${data.summary.systemStatus} · Last Plan Generated: ${formatDateTime(data.summary.lastPlanGeneratedAt)}`}
      />

      <div className="flex flex-col gap-4 p-5 sm:p-6">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <MetricCard label="Critical Needs" value={data.summary.criticalNeeds} icon={AlertTriangle} tone="critical" />
          <MetricCard label="Active Deliveries" value={data.summary.activeDeliveries} icon={Truck} tone="primary" />
          <MetricCard label="Resource Coverage" value={`${data.summary.resourceCoveragePct}%`} icon={PieChart} tone="neutral" />
          <MetricCard label="Vehicles Available" value={data.summary.vehiclesAvailable} icon={CarFront} tone="neutral" />
          <MetricCard label="At-Risk Deliveries" value={data.summary.atRiskDeliveries} icon={Clock3} tone="warning" />
        </div>

        <section className="flex flex-col gap-2.5">
          <h2 className="flex items-center gap-1.5 text-sm font-semibold text-text">
            Delivery Time Watch
            <span className="text-[11px] font-normal text-muted">
              · most time-sensitive active deliveries, by real ETA/deadline
            </span>
          </h2>
          <DeliveryTimeWatch deliveries={data.deliveries} onSelect={setSelectedDelivery} />
        </section>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="h-[420px] overflow-hidden rounded-sm border border-border shadow-card lg:col-span-2">
            <ReliefMap
              requests={data.requests}
              sources={data.sources}
              vehicles={data.vehicles}
              routes={data.routes}
              roadNodes={data.roadNodes}
              roadEdges={data.roadEdges}
              deliveries={data.deliveries}
              layers={DEFAULT_LAYER_STATE}
              onSelectRequest={setSelectedRequest}
            />
          </div>
          <AlgorithmPanel snapshot={data.snapshot} />
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <section className="flex flex-col gap-2.5">
            <h2 className="text-sm font-semibold text-text">Critical Needs</h2>
            <DataTable columns={needsColumns} rows={criticalNeeds} rowKey={(r) => r.id} onRowClick={setSelectedRequest} />
          </section>
          <section className="flex flex-col gap-2.5">
            <h2 className="text-sm font-semibold text-text">Active Deliveries</h2>
            <DataTable columns={deliveryColumns} rows={activeDeliveries} rowKey={(d) => d.id} onRowClick={setSelectedDelivery} />
          </section>
        </div>

        <section className="flex flex-col gap-2.5">
          <h2 className="text-sm font-semibold text-text">Bottlenecks</h2>
          <BottleneckPanel bottlenecks={data.bottlenecks} />
        </section>
      </div>

      <Drawer
        open={!!selectedRequest}
        onClose={() => setSelectedRequest(null)}
        title={selectedRequest?.areaName ?? ""}
        subtitle={selectedRequest ? `${selectedRequest.id} · ${selectedRequest.resource}` : undefined}
      >
        {selectedRequest && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <PriorityBadge level={selectedRequest.urgency} />
              <StatusBadge kind="request" status={selectedRequest.status} />
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-[11px] text-muted">People Affected</dt>
                <dd className="font-medium tabular">{formatNumber(selectedRequest.peopleAffected)}</dd>
              </div>
              <div>
                <dt className="text-[11px] text-muted">Deadline</dt>
                <dd className="font-medium">
                  <DeadlineIndicator deadlineIso={selectedRequest.deadline} />
                </dd>
              </div>
            </dl>
            <UnmetDemandPanel request={selectedRequest} />
          </div>
        )}
      </Drawer>

      <Drawer
        open={!!selectedDelivery}
        onClose={() => setSelectedDelivery(null)}
        title={selectedDelivery?.id ?? ""}
        subtitle={selectedDelivery ? `${selectedDelivery.originName} → ${selectedDelivery.destinationName}` : undefined}
      >
        {selectedDelivery && <Timeline events={selectedDelivery.events} />}
      </Drawer>
    </div>
  );
}
