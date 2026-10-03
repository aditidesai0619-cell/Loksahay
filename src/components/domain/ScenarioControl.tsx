import { Trash2 } from "lucide-react";
import type { ScenarioAction, ScenarioControlType } from "@/types";

export const SCENARIO_TYPES: ScenarioControlType[] = [
  "Block Road",
  "Remove Vehicle",
  "Reduce Inventory",
  "Add Affected Area",
  "Increase Urgency",
];

interface TargetOption {
  id: string;
  label: string;
}

interface ScenarioControlProps {
  action: ScenarioAction;
  targetOptions: TargetOption[];
  onTypeChange: (type: ScenarioControlType) => void;
  onTargetChange: (targetId: string, targetLabel: string) => void;
  onValueChange?: (value: number) => void;
  onRemove: () => void;
}

export function ScenarioControl({ action, targetOptions, onTypeChange, onTargetChange, onValueChange, onRemove }: ScenarioControlProps) {
  const needsValue = action.type === "Reduce Inventory";

  return (
    <div className="flex flex-wrap items-center gap-2.5 rounded-sm border border-border bg-surface p-3">
      <select
        value={action.type}
        onChange={(e) => onTypeChange(e.target.value as ScenarioControlType)}
        className="rounded-sm border border-border bg-surface px-2.5 py-1.5 text-xs font-medium text-text"
      >
        {SCENARIO_TYPES.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      <select
        value={action.targetId}
        onChange={(e) => {
          const opt = targetOptions.find((o) => o.id === e.target.value);
          if (opt) onTargetChange(opt.id, opt.label);
        }}
        className="min-w-[180px] flex-1 rounded-sm border border-border bg-surface px-2.5 py-1.5 text-xs text-text"
      >
        <option value="" disabled>
          Select target…
        </option>
        {targetOptions.map((o) => (
          <option key={o.id} value={o.id}>
            {o.label}
          </option>
        ))}
      </select>

      {needsValue && (
        <div className="flex items-center gap-1.5">
          <input
            type="number"
            min={0}
            max={100}
            value={action.value ?? 30}
            onChange={(e) => onValueChange?.(Number(e.target.value))}
            className="w-16 rounded-sm border border-border bg-surface px-2 py-1.5 text-xs tabular text-text"
          />
          <span className="text-xs text-muted">% reduction</span>
        </div>
      )}

      <button onClick={onRemove} className="ml-auto rounded-sm p-1.5 text-muted hover:bg-surface-sunken hover:text-critical">
        <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
      </button>
    </div>
  );
}
