import { clsx, type ClassValue } from "clsx";
import type {
  AllocationStatus,
  BottleneckImpact,
  DeliveryStatus,
  RequestStatus,
  RoadCondition,
  UrgencyLevel,
  VehicleStatus,
} from "@/types";

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-IN").format(value);
}

// Countdown helpers are anchored to the real current time — deadlines and
// ETAs now come from a live backend relative to when its plan was
// generated, so "at risk"/"overdue" should track the visitor's real clock.
export function formatCountdown(iso: string, fromIso?: string): string {
  const target = new Date(iso).getTime();
  const from = fromIso ? new Date(fromIso).getTime() : Date.now();
  const diffMin = Math.round((target - from) / 60_000);
  const overdue = diffMin < 0;
  const abs = Math.abs(diffMin);
  const h = Math.floor(abs / 60);
  const m = abs % 60;
  const label = `${h > 0 ? `${h}h ` : ""}${m}m`;
  return overdue ? `${label} overdue` : `in ${label}`;
}

export function minutesUntil(iso: string, fromIso?: string): number {
  const target = new Date(iso).getTime();
  const from = fromIso ? new Date(fromIso).getTime() : Date.now();
  return Math.round((target - from) / 60_000);
}

export type DeliveryTimeTier = "On Track" | "Approaching Deadline" | "Deadline At Risk";

// Same thresholds DeadlineIndicator already uses (20-minute ETA/deadline
// buffer, 60-minute "soon" window) — this just labels the existing
// real-data "at risk" signal into the Dashboard's 3-tier Delivery Time
// Watch rather than recomputing a different notion of risk.
export function deliveryTimeTier(deadlineIso: string, etaIso?: string, meetsDeadline?: boolean): DeliveryTimeTier {
  const minsLeft = minutesUntil(deadlineIso);
  const overdue = minsLeft < 0;
  const bufferAtRisk = etaIso ? minutesUntil(deadlineIso) - minutesUntil(etaIso) < 20 : minsLeft < 60;
  const atRisk = meetsDeadline === false || overdue || bufferAtRisk;
  if (atRisk) return "Deadline At Risk";
  if (minsLeft < 60) return "Approaching Deadline";
  return "On Track";
}

export const URGENCY_ORDER: UrgencyLevel[] = ["Critical", "High", "Medium", "Low"];

export function urgencyTone(level: UrgencyLevel): "critical" | "warning" | "secondary" | "muted" {
  switch (level) {
    case "Critical":
      return "critical";
    case "High":
      return "warning";
    case "Medium":
      return "secondary";
    case "Low":
      return "muted";
  }
}

export function requestStatusTone(status: RequestStatus): "primary" | "warning" | "critical" {
  switch (status) {
    case "Fulfilled":
      return "primary";
    case "Partial":
      return "warning";
    case "Unfulfilled":
      return "critical";
  }
}

export function vehicleStatusTone(status: VehicleStatus): "primary" | "accent" | "secondary" | "muted" | "critical" {
  switch (status) {
    case "Available":
      return "secondary";
    case "Assigned":
      return "accent";
    case "In Transit":
      return "accent";
    case "Delivered":
      return "primary";
    case "Unavailable":
      return "critical";
  }
}

export function deliveryStatusTone(status: DeliveryStatus): "primary" | "accent" | "secondary" {
  switch (status) {
    case "Delivered":
      return "primary";
    case "Arrived":
      return "primary";
    case "In Transit":
    case "Picked Up":
      return "accent";
    case "Accepted":
    case "Assigned":
      return "secondary";
  }
}

export function allocationStatusTone(status: AllocationStatus): "primary" | "accent" | "secondary" | "critical" {
  switch (status) {
    case "Accepted":
      return "primary";
    case "Modified":
      return "accent";
    case "Proposed":
      return "secondary";
    case "Rejected":
      return "critical";
  }
}

export function roadConditionTone(condition: RoadCondition): "primary" | "warning" | "critical" {
  switch (condition) {
    case "Clear":
      return "primary";
    case "Degraded":
      return "warning";
    case "Blocked":
      return "critical";
  }
}

export function bottleneckImpactTone(impact: BottleneckImpact): "critical" | "warning" | "secondary" {
  switch (impact) {
    case "Critical":
      return "critical";
    case "High":
      return "warning";
    case "Medium":
      return "secondary";
  }
}
