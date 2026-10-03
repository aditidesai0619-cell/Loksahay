import type {
  AllocationStatus,
  DeliveryStatus,
  RequestStatus,
  RoadCondition,
  VehicleStatus,
} from "@/types";
import {
  allocationStatusTone,
  deliveryStatusTone,
  requestStatusTone,
  roadConditionTone,
  vehicleStatusTone,
} from "@/lib/utils";
import { Badge } from "./Badge";

type StatusBadgeProps =
  | { kind: "request"; status: RequestStatus }
  | { kind: "vehicle"; status: VehicleStatus }
  | { kind: "delivery"; status: DeliveryStatus }
  | { kind: "allocation"; status: AllocationStatus }
  | { kind: "road"; status: RoadCondition };

export function StatusBadge(props: StatusBadgeProps) {
  switch (props.kind) {
    case "request":
      return <Badge tone={requestStatusTone(props.status)}>{props.status}</Badge>;
    case "vehicle":
      return <Badge tone={vehicleStatusTone(props.status)}>{props.status}</Badge>;
    case "delivery":
      return <Badge tone={deliveryStatusTone(props.status)}>{props.status}</Badge>;
    case "allocation":
      return <Badge tone={allocationStatusTone(props.status)}>{props.status}</Badge>;
    case "road":
      return <Badge tone={roadConditionTone(props.status)}>{props.status}</Badge>;
  }
}
