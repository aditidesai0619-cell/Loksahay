import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { AnalyticsResult } from "@/types";
import { service, ApiError } from "@/data/service";
import { formatNumber, formatTime } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { MetricCard } from "@/components/common/MetricCard";
import { LoadingState, ErrorState } from "@/components/common/States";
import { Badge } from "@/components/common/Badge";

const COLOR_LOKSAHAY = "#1a7048";
const COLOR_BASELINE = "#b8862f";
const GRID_COLOR = "#dddcd5";

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-sm border border-border bg-surface px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-medium text-text">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="flex items-center gap-1.5 text-muted">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color }} />
          {p.name}: <span className="font-medium tabular text-text">{p.value}</span>
        </p>
      ))}
    </div>
  );
}

export function Analytics() {
  const [data, setData] = useState<AnalyticsResult | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    service
      .getAnalytics()
      .then(setData)
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not reach the backend"));
  }, []);

  if (loadError) {
    return (
      <div className="flex flex-col">
        <PageHeader title="Analytics" />
        <div className="p-5 sm:p-6">
          <ErrorState title="Could not load analytics" description={loadError} />
        </div>
      </div>
    );
  }

  if (!data) {
    return <LoadingState title="Loading analytics…" className="h-full" />;
  }

  const comparisonData = [
    { metric: "Demand Fulfilled", LokSahay: data.loksahay.metrics.demandFulfilledPct, Baseline: data.baseline.metrics.demandFulfilledPct },
    {
      metric: "Critical Demand Fulfilled",
      LokSahay: data.loksahay.metrics.criticalDemandFulfilledPct,
      Baseline: data.baseline.metrics.criticalDemandFulfilledPct,
    },
    { metric: "On-Time Delivery", LokSahay: data.loksahay.metrics.onTimeDeliveryPct, Baseline: data.baseline.metrics.onTimeDeliveryPct },
  ];

  const historyData = data.history.map((h) => ({
    time: formatTime(h.timestamp),
    "Demand Fulfilled %": Math.round(h.demandFulfilledPct * 10) / 10,
    "On-Time Delivery %": Math.round(h.onTimeDeliveryPct * 10) / 10,
  }));

  return (
    <div className="flex flex-col">
      <PageHeader title="Analytics" subtitle="Allocation performance for the current plan" />

      <div className="flex flex-col gap-5 p-5 sm:p-6">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <MetricCard label="Demand Fulfilled" value={`${data.current.demandFulfilledPct}%`} tone="primary" />
          <MetricCard label="Critical Demand Fulfilled" value={`${data.current.criticalDemandFulfilledPct}%`} tone="primary" />
          <MetricCard label="On-Time Delivery" value={`${data.current.onTimeDeliveryPct}%`} tone="primary" />
          <MetricCard label="Total Distance" value={formatNumber(data.current.totalDistanceKm)} unit="km" />
          <MetricCard label="Vehicle Trips" value={data.current.vehicleTrips} />
          <MetricCard label="Unmet Demand" value={formatNumber(data.current.unmetDemandUnits)} unit="units" tone="critical" />
        </div>

        <section className="flex flex-col gap-3 rounded-sm border border-border bg-surface p-4 shadow-card">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold text-text">LokSahay Allocation vs. Simple Baseline</h2>
              <p className="text-[11px] text-muted">Baseline: nearest-source / first-come allocation, no deadline or feasibility awareness</p>
            </div>
            <Badge tone="secondary">Both run live against the same current dataset</Badge>
          </div>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }} barGap={6}>
                <CartesianGrid vertical={false} stroke={GRID_COLOR} />
                <XAxis dataKey="metric" tick={{ fontSize: 11, fill: "#72766f" }} axisLine={{ stroke: GRID_COLOR }} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#72766f" }} axisLine={false} tickLine={false} width={34} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(37,77,58,0.05)" }} />
                <Legend wrapperStyle={{ fontSize: 12, color: "#72766f" }} />
                <Bar dataKey="LokSahay" fill={COLOR_LOKSAHAY} radius={[3, 3, 0, 0]} maxBarSize={40} />
                <Bar dataKey="Baseline" fill={COLOR_BASELINE} radius={[3, 3, 0, 0]} maxBarSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-1 gap-2 border-t border-border pt-3 text-xs sm:grid-cols-3">
            <CompareRow label="Total Distance" loksahay={`${formatNumber(data.loksahay.metrics.totalDistanceKm)} km`} baseline={`${formatNumber(data.baseline.metrics.totalDistanceKm)} km`} />
            <CompareRow label="Vehicle Trips" loksahay={String(data.loksahay.metrics.vehicleTrips)} baseline={String(data.baseline.metrics.vehicleTrips)} />
            <CompareRow label="Unmet Demand" loksahay={formatNumber(data.loksahay.metrics.unmetDemandUnits)} baseline={formatNumber(data.baseline.metrics.unmetDemandUnits)} />
          </div>
        </section>

        <section className="flex flex-col gap-3 rounded-sm border border-border bg-surface p-4 shadow-card">
          <div>
            <h2 className="text-sm font-semibold text-text">Plan Performance Over Time</h2>
            <p className="text-[11px] text-muted">Recorded from every real allocation run, replan and scenario apply this session</p>
          </div>
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historyData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke={GRID_COLOR} />
                <XAxis dataKey="time" tick={{ fontSize: 11, fill: "#72766f" }} axisLine={{ stroke: GRID_COLOR }} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#72766f" }} axisLine={false} tickLine={false} width={34} />
                <Tooltip content={<ChartTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12, color: "#72766f" }} />
                <Line type="monotone" dataKey="Demand Fulfilled %" stroke={COLOR_LOKSAHAY} strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="On-Time Delivery %" stroke={COLOR_BASELINE} strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
    </div>
  );
}

function CompareRow({ label, loksahay, baseline }: { label: string; loksahay: string; baseline: string }) {
  return (
    <div className="flex items-center justify-between rounded-sm bg-surface-sunken px-3 py-2">
      <span className="text-muted">{label}</span>
      <span className="flex items-center gap-2.5">
        <span className="font-medium text-text">{loksahay}</span>
        <span className="text-muted">vs</span>
        <span className="text-muted">{baseline}</span>
      </span>
    </div>
  );
}
