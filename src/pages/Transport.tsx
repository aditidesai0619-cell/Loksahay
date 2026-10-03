import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Map as MapIcon, ArrowRight, TriangleAlert, MapPin } from "lucide-react";
import type { Delivery, DeliveryPartner, DeliveryStatus, Vehicle, VehicleStatus } from "@/types";
import { service, ApiError } from "@/data/service";
import { formatNumber, formatTime, cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { MetricCard } from "@/components/common/MetricCard";
import { LoadingState, ErrorState, EmptyState } from "@/components/common/States";
import { Drawer } from "@/components/common/Drawer";
import { StatusBadge } from "@/components/common/StatusBadge";
import { DeadlineIndicator } from "@/components/common/DeadlineIndicator";
import { Timeline } from "@/components/common/Timeline";
import { VehicleCard } from "@/components/domain/VehicleCard";
import { PartnerCard } from "@/components/domain/PartnerCard";

const FLEET_STATUSES: VehicleStatus[] = ["Available", "Assigned", "In Transit", "Delivered", "Unavailable"];

const DELIVERY_LIFECYCLE: DeliveryStatus[] = ["Assigned", "Accepted", "Picked Up", "In Transit", "Arrived", "Delivered"];

type Tab = "fleet" | "partners";

function locationLabel(d: Delivery): string {
  if (d.status === "Delivered") return d.destinationName;
  if (d.status === "In Transit" || d.status === "Arrived") return `En route to ${d.destinationName}`;
  return d.originName;
}

export function Transport() {
  const [vehicles, setVehicles] = useState<Vehicle[] | null>(null);
  const [deliveries, setDeliveries] = useState<Delivery[] | null>(null);
  const [partners, setPartners] = useState<DeliveryPartner[] | null>(null);
  const [tab, setTab] = useState<Tab>("fleet");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [advancing, setAdvancing] = useState(false);
  const [advanceError, setAdvanceError] = useState<string | null>(null);

  function load() {
    setLoadError(null);
    Promise.all([service.getVehicles(), service.getDeliveries(), service.getPartners()])
      .then(([v, d, p]) => {
        setVehicles(v);
        setDeliveries(d);
        setPartners(p);
      })
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend"));
  }

  useEffect(() => {
    load();
  }, []);

  const deliveryByVehicle = useMemo(() => {
    const map = new Map<string, Delivery>();
    deliveries?.forEach((d) => map.set(d.vehicleId, d));
    return map;
  }, [deliveries]);

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="Transport Center" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load transport center" description={loadError} />
        </div>
      </div>
    );
  }

  if (!vehicles || !deliveries || !partners) {
    return <LoadingState title="Loading transport center…" className="h-full" />;
  }

  const selected = vehicles.find((v) => v.id === selectedId) ?? null;
  const selectedDelivery = selected ? deliveryByVehicle.get(selected.id) : undefined;
  const selectedPartner = selected ? partners.find((p) => p.name === selected.partner) : undefined;
  const nextStage = selectedDelivery
    ? DELIVERY_LIFECYCLE[DELIVERY_LIFECYCLE.indexOf(selectedDelivery.status) + 1]
    : undefined;
  const deliveryAtRisk = selectedDelivery ? !selectedDelivery.meetsDeadline : false;

  async function handleAdvance() {
    if (!selectedDelivery || !nextStage) return;
    setAdvancing(true);
    setAdvanceError(null);
    try {
      await service.advanceDeliveryStatus(selectedDelivery.id, nextStage);
      load();
    } catch (err) {
      setAdvanceError(err instanceof ApiError ? err.message : "Could not advance delivery status");
    } finally {
      setAdvancing(false);
    }
  }

  return (
    <div className="flex flex-col">
      <PageHeader title="Transport Center" subtitle={`${vehicles.length} vehicles · ${partners.length} delivery partners`} />

      <div className="flex gap-1.5 border-b border-border bg-surface px-5 py-2.5 shadow-card sm:px-6">
        <button
          onClick={() => setTab("fleet")}
          className={cn(
            "rounded-sm px-2.5 py-1 text-xs font-medium",
            tab === "fleet" ? "border border-primary/30 bg-primary-tint text-primary-dark" : "border border-border text-muted",
          )}
        >
          Fleet
        </button>
        <button
          onClick={() => setTab("partners")}
          className={cn(
            "rounded-sm px-2.5 py-1 text-xs font-medium",
            tab === "partners" ? "border border-primary/30 bg-primary-tint text-primary-dark" : "border border-border text-muted",
          )}
        >
          Delivery Partners
        </button>
      </div>

      {tab === "fleet" ? (
        <div className="flex flex-col gap-4 p-5 sm:p-6">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {FLEET_STATUSES.map((status) => (
              <MetricCard
                key={status}
                label={status}
                value={vehicles.filter((v) => v.status === status).length}
                tone={status === "Unavailable" ? "critical" : status === "Available" ? "primary" : "neutral"}
              />
            ))}
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {vehicles.map((vehicle) => (
              <VehicleCard
                key={vehicle.id}
                vehicle={vehicle}
                delivery={deliveryByVehicle.get(vehicle.id)}
                onClick={() => setSelectedId(vehicle.id)}
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-4 p-5 sm:p-6">
          {partners.length === 0 ? (
            <EmptyState title="No delivery partners on record" />
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {partners.map((p) => (
                <PartnerCard key={p.id} partner={p} onSelectVehicle={setSelectedId} />
              ))}
            </div>
          )}
        </div>
      )}

      <Drawer
        open={!!selected}
        onClose={() => {
          setSelectedId(null);
          setAdvanceError(null);
        }}
        title={selected?.id ?? ""}
        subtitle={selected ? `${selected.partner} · ${selected.type}` : undefined}
      >
        {selected && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <StatusBadge kind="vehicle" status={selected.status} />
              {selectedDelivery && (
                <Link
                  to={`/map?routeId=${selectedDelivery.routeId}`}
                  className="flex items-center gap-1 text-xs font-medium text-primary hover:text-primary-dark"
                >
                  <MapIcon className="h-3.5 w-3.5" strokeWidth={1.75} />
                  View on Map
                </Link>
              )}
            </div>

            {deliveryAtRisk && (
              <div className="flex items-center justify-between gap-2 rounded-sm border border-critical/30 bg-critical-tint px-3 py-2">
                <span className="flex items-center gap-1.5 text-xs font-medium text-critical">
                  <TriangleAlert className="h-3.5 w-3.5" strokeWidth={1.75} />
                  Deadline at risk
                </span>
                <Link to="/replanning" className="text-xs font-medium text-critical underline hover:no-underline">
                  Open Replanning
                </Link>
              </div>
            )}

            {selectedPartner && (
              <div>
                <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-muted">Delivery Partner</p>
                <p className="text-sm font-medium text-text">{selectedPartner.name}</p>
                <p className="text-xs text-muted">{selectedPartner.contactPerson} · {selectedPartner.phone}</p>
              </div>
            )}

            {selectedDelivery ? (
              <>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <dt className="text-[11px] text-muted">Origin</dt>
                    <dd className="font-medium">{selectedDelivery.originName}</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] text-muted">Destination</dt>
                    <dd className="font-medium">{selectedDelivery.destinationName}</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] text-muted">Distance</dt>
                    <dd className="font-medium tabular">{selectedDelivery.distanceKm} km</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] text-muted">ETA</dt>
                    <dd className="font-medium tabular">{formatTime(selectedDelivery.etaIso)}</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] text-muted">Deadline</dt>
                    <dd>
                      <DeadlineIndicator
                        deadlineIso={selectedDelivery.deadlineIso}
                        etaIso={selectedDelivery.etaIso}
                        atRisk={!selectedDelivery.meetsDeadline}
                      />
                    </dd>
                  </div>
                  <div className="col-span-2">
                    <dt className="text-[11px] text-muted">Current / Last Known Location</dt>
                    <dd className="flex items-center gap-1.5 font-medium">
                      <MapPin className="h-3.5 w-3.5 flex-none text-secondary" strokeWidth={1.75} />
                      {locationLabel(selectedDelivery)}
                      {selectedDelivery.currentLocation && (
                        <span className="tabular text-[11px] font-normal text-muted">
                          ({selectedDelivery.currentLocation.lat.toFixed(3)}, {selectedDelivery.currentLocation.lng.toFixed(3)})
                        </span>
                      )}
                    </dd>
                  </div>
                </dl>

                <div>
                  <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-muted">Cargo</p>
                  <div className="flex flex-col gap-1">
                    {selectedDelivery.cargo.map((c) => (
                      <p key={c.resource} className="text-sm text-text">
                        {c.resource} · {formatNumber(c.quantity)} {c.unit}
                      </p>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="mb-1.5 flex items-center justify-between">
                    <p className="text-[11px] font-medium uppercase tracking-wide text-muted">Tracking</p>
                    {nextStage && (
                      <button
                        onClick={handleAdvance}
                        disabled={advancing}
                        className="flex items-center gap-1 rounded-sm bg-primary px-2.5 py-1 text-xs font-medium text-background hover:bg-primary-dark disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {advancing ? "Updating…" : `Advance to ${nextStage}`}
                        {!advancing && <ArrowRight className="h-3 w-3" strokeWidth={2} />}
                      </button>
                    )}
                  </div>
                  {advanceError && <p className="mb-2 text-xs text-critical">{advanceError}</p>}
                  <Timeline events={selectedDelivery.events} />
                </div>
              </>
            ) : (
              <p className="text-xs text-muted">No active delivery assigned to this vehicle.</p>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}
