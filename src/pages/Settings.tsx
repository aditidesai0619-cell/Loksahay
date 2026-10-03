import { useEffect, useState } from "react";
import type { AlgorithmSnapshot, PriorityWeights } from "@/types";
import { service, ApiError } from "@/data/service";
import { PageHeader } from "@/components/layout/PageHeader";
import { LoadingState, ErrorState } from "@/components/common/States";
import { Badge } from "@/components/common/Badge";

const WEIGHT_LABELS: { key: keyof PriorityWeights; label: string; description: string }[] = [
  { key: "urgency", label: "Urgency", description: "Weight given to request urgency level (Critical → Low)" },
  { key: "populationNeed", label: "Population Need", description: "Weight given to number of people affected" },
  { key: "supplyDeficit", label: "Supply Deficit", description: "Weight given to the gap between required and available supply" },
  { key: "accessibility", label: "Accessibility", description: "Weight given to route feasibility and travel time" },
];

export function SettingsPage() {
  const [snapshot, setSnapshot] = useState<AlgorithmSnapshot | null>(null);
  const [weights, setWeights] = useState<PriorityWeights | null>(null);
  const [minimumCoveragePct, setMinimumCoveragePct] = useState(60);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  function load() {
    setLoadError(null);
    service
      .getAlgorithmSnapshot()
      .then((s) => {
        setSnapshot(s);
        setWeights(s.priorityWeights);
        setMinimumCoveragePct(s.minimumCoveragePct);
      })
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend"));
  }

  useEffect(() => {
    load();
  }, []);

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="Settings" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load algorithm configuration" description={loadError} />
        </div>
      </div>
    );
  }

  if (!snapshot || !weights) {
    return <LoadingState title="Loading settings…" className="h-full" />;
  }

  const total = Object.values(weights).reduce((s, v) => s + v, 0);

  function updateWeight(key: keyof PriorityWeights, value: number) {
    setSaved(false);
    setWeights((prev) => (prev ? { ...prev, [key]: value / 100 } : prev));
  }

  async function handleSave() {
    if (!weights) return;
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await service.updateAlgorithmWeights({ ...weights, minimumCoveragePct });
      setSnapshot(updated);
      setWeights(updated.priorityWeights);
      setMinimumCoveragePct(updated.minimumCoveragePct);
      setSaved(true);
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message : "Could not save — try again");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col">
      <PageHeader title="Settings" subtitle="Allocation engine configuration — prototype, configurable priority model" />

      <div className="flex flex-col gap-4 p-5 sm:p-6">
        <section className="rounded-sm border border-border bg-surface p-4 shadow-card">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-text">Priority Model Weights</h2>
              <p className="text-[11px] text-muted">
                Adjust how the allocation engine ranks competing requests. This is a prototype, configurable priority
                model — not an official disaster-response standard.
              </p>
            </div>
            <Badge tone={Math.round(total * 100) === 100 ? "primary" : "warning"}>{Math.round(total * 100)}% total</Badge>
          </div>

          <div className="flex flex-col gap-4">
            {WEIGHT_LABELS.map(({ key, label, description }) => (
              <div key={key} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-text">{label}</span>
                  <span className="tabular text-muted">{Math.round(weights[key] * 100)}%</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={Math.round(weights[key] * 100)}
                  onChange={(e) => updateWeight(key, Number(e.target.value))}
                  className="h-1.5 w-full accent-primary"
                />
                <p className="text-[11px] text-muted">{description}</p>
              </div>
            ))}

            <div className="flex flex-col gap-1.5 border-t border-border pt-4">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-text">Minimum Coverage</span>
                <span className="tabular text-muted">{minimumCoveragePct}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                value={minimumCoveragePct}
                onChange={(e) => {
                  setSaved(false);
                  setMinimumCoveragePct(Number(e.target.value));
                }}
                className="h-1.5 w-full accent-primary"
              />
              <p className="text-[11px] text-muted">
                Share of a feasible request&apos;s requirement reserved for it before higher-priority requests can take
                everything in the uncapped top-up pass (the fairness guarantee).
              </p>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-3 border-t border-border pt-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-sm bg-primary px-3.5 py-1.5 text-xs font-semibold text-background hover:bg-primary-dark disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save Configuration"}
            </button>
            {saved && !saving && <span className="text-xs text-primary">Saved — applied on the next allocation run.</span>}
            {saveError && <span className="text-xs text-critical">{saveError}</span>}
          </div>

          <p className="mt-3 border-t border-border pt-3 text-[11px] text-muted">
            Saved weights are persisted on the backend (<code>GET/PUT /algorithm/config</code>) and used by every
            subsequent allocation run — they do not retroactively change allocations already proposed or accepted.
          </p>
        </section>

        <section className="rounded-sm border border-border bg-surface p-4 shadow-card">
          <h2 className="text-sm font-semibold text-text">About</h2>
          <p className="mt-1 text-xs text-muted">
            LokSahay is an algorithmic decision-support system for coordinating disaster-relief resources, vehicles, routes
            and delivery deadlines. Built for the APSH 2026 demonstration, backed by a real FastAPI allocation engine.
          </p>
        </section>
      </div>
    </div>
  );
}
