import type { UrgencyLevel } from "@/types";
import { urgencyTone } from "@/lib/utils";
import { Badge } from "./Badge";

export function PriorityBadge({ level }: { level: UrgencyLevel }) {
  return (
    <Badge tone={urgencyTone(level)} dot>
      {level}
    </Badge>
  );
}
