import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export type BadgeTone = "primary" | "accent" | "warning" | "critical" | "secondary" | "muted";

const TONE_CLASSES: Record<BadgeTone, string> = {
  primary: "bg-primary-tint text-primary-dark border-primary/20",
  accent: "bg-accent-tint text-accent-dark border-accent/25",
  warning: "bg-warning-tint text-[#7a5717] border-warning/30",
  critical: "bg-critical-tint text-critical border-critical/25",
  secondary: "bg-secondary-tint text-secondary border-secondary/20",
  muted: "bg-surface-sunken text-muted border-border",
};

const DOT_CLASSES: Record<BadgeTone, string> = {
  primary: "bg-primary",
  accent: "bg-accent",
  warning: "bg-warning",
  critical: "bg-critical",
  secondary: "bg-secondary",
  muted: "bg-muted",
};

interface BadgeProps {
  tone?: BadgeTone;
  children: ReactNode;
  dot?: boolean;
  className?: string;
}

export function Badge({ tone = "muted", children, dot = false, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-xs font-medium leading-5 whitespace-nowrap",
        TONE_CLASSES[tone],
        className,
      )}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full", DOT_CLASSES[tone])} />}
      {children}
    </span>
  );
}
