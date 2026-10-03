import { Phone, User, Truck } from "lucide-react";
import type { DeliveryPartner } from "@/types";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Badge } from "@/components/common/Badge";

interface PartnerCardProps {
  partner: DeliveryPartner;
  onSelectVehicle?: (vehicleId: string) => void;
}

export function PartnerCard({ partner, onSelectVehicle }: PartnerCardProps) {
  return (
    <div className="flex flex-col gap-3 rounded-sm border border-border bg-surface p-4 shadow-card">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-text">{partner.name}</p>
          <p className="text-[11px] text-muted">{partner.id}</p>
        </div>
        <div className="flex gap-1.5">
          <Badge tone="primary">{partner.activeDeliveries} active</Badge>
          <Badge tone="secondary">{partner.completedDeliveries} completed</Badge>
        </div>
      </div>

      <div className="flex flex-col gap-1 border-t border-border pt-2.5 text-xs text-secondary">
        <div className="flex items-center gap-1.5">
          <User className="h-3.5 w-3.5 flex-none text-muted" strokeWidth={1.75} />
          {partner.contactPerson}
        </div>
        <div className="flex items-center gap-1.5">
          <Phone className="h-3.5 w-3.5 flex-none text-muted" strokeWidth={1.75} />
          {partner.phone}
        </div>
      </div>

      <div className="flex flex-col gap-1.5 border-t border-border pt-2.5">
        <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted">
          <Truck className="h-3.5 w-3.5" strokeWidth={1.75} />
          Fleet ({partner.vehicles.length})
        </p>
        {partner.vehicles.map((v) => (
          <button
            key={v.vehicleId}
            onClick={() => onSelectVehicle?.(v.vehicleId)}
            className="flex items-center justify-between gap-2 rounded-sm px-2 py-1.5 text-left text-xs hover:bg-surface-sunken"
          >
            <span className="font-medium text-text">
              {v.vehicleId} <span className="font-normal text-muted">{v.type} · {v.capacityKg}kg</span>
            </span>
            <span className="flex items-center gap-2">
              {v.currentDeliveryId && <span className="text-muted">{v.currentDeliveryId}</span>}
              <StatusBadge kind="vehicle" status={v.status} />
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
