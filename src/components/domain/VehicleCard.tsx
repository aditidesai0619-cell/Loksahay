import { Truck, Bike, CarFront } from "lucide-react";
import type { Delivery, Vehicle } from "@/types";
import { formatTime, cn } from "@/lib/utils";
import { StatusBadge } from "@/components/common/StatusBadge";
import { DeadlineIndicator } from "@/components/common/DeadlineIndicator";

const TYPE_ICON = { Truck, "Mini-Van": CarFront, "4x4": CarFront, Motorbike: Bike } as const;

export function VehicleCard({ vehicle, delivery, onClick }: { vehicle: Vehicle; delivery?: Delivery; onClick?: () => void }) {
  const Icon = TYPE_ICON[vehicle.type];
  // cargoWeightKg is computed by the backend (resource-specific kg/unit —
  // Medicine/Essentials/Food/Water all convert differently), not assumed
  // here, so this load % always matches the real vehicle-capacity check
  // the allocation engine applies.
  const loadPct = Math.min(100, Math.round((vehicle.cargoWeightKg / vehicle.capacityKg) * 100));

  return (
    <button
      onClick={onClick}
      className="flex flex-col gap-3 rounded-sm border border-border bg-surface p-4 text-left shadow-card transition-colors hover:border-primary/40 hover:bg-primary-tint/30"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 flex-none items-center justify-center rounded-sm bg-surface-sunken">
            <Icon className="h-4 w-4 text-primary" strokeWidth={1.75} />
          </div>
          <div>
            <p className="text-sm font-semibold text-text">{vehicle.id}</p>
            <p className="text-[11px] text-muted">{vehicle.partner}</p>
          </div>
        </div>
        <StatusBadge kind="vehicle" status={vehicle.status} />
      </div>

      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between text-[11px] text-muted">
          <span>Cargo load</span>
          <span className="tabular">{vehicle.cargoWeightKg} / {vehicle.capacityKg} kg</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-surface-sunken">
          <div className={cn("h-full bg-secondary", loadPct > 85 && "bg-accent")} style={{ width: `${loadPct}%` }} />
        </div>
      </div>

      {delivery ? (
        <div className="flex items-center justify-between gap-2 border-t border-border pt-2.5">
          <div className="text-xs">
            <p className="font-medium text-text">→ {delivery.destinationName}</p>
            <p className="text-[11px] text-muted">ETA {formatTime(delivery.etaIso)}</p>
          </div>
          <DeadlineIndicator
            deadlineIso={delivery.deadlineIso}
            etaIso={delivery.etaIso}
            atRisk={!delivery.meetsDeadline}
            className="items-end"
          />
        </div>
      ) : (
        <p className="border-t border-border pt-2.5 text-[11px] text-muted">No active assignment</p>
      )}
    </button>
  );
}
