import { useEffect, useState } from "react";
import { Menu, MapPin, Clock } from "lucide-react";
import type { Coordinator, OperationalSummary } from "@/types";
import { service } from "@/data/service";
import { formatTime } from "@/lib/utils";
import { Badge } from "@/components/common/Badge";
import { Logo } from "@/components/common/Logo";

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const [summary, setSummary] = useState<OperationalSummary | null>(null);
  const [coordinator, setCoordinator] = useState<Coordinator | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    service.getOperationalSummary().then(setSummary).catch(() => setOffline(true));
    service.getCoordinator().then(setCoordinator).catch(() => setOffline(true));
  }, []);

  const statusTone: "primary" | "warning" | "critical" =
    summary?.systemStatus === "Operational" ? "primary" : summary?.systemStatus === "Degraded" ? "warning" : "critical";

  return (
    <header className="flex h-16 flex-none items-center justify-between gap-3 border-b border-border bg-surface px-4 shadow-[0_1px_0_rgba(32,35,31,0.03)] sm:px-6">
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onMenuClick}
          className="rounded-md p-1.5 text-secondary hover:bg-surface-sunken md:hidden"
          aria-label="Open navigation"
        >
          <Menu className="h-5 w-5" strokeWidth={1.75} />
        </button>
        <Logo size={24} className="md:hidden" />
        <div className="flex items-center gap-2 min-w-0 rounded-md border border-border bg-surface-sunken px-2.5 py-1.5">
          <MapPin className="h-3.5 w-3.5 flex-none text-primary" strokeWidth={1.75} />
          <span className="truncate text-sm font-semibold text-text">
            {offline ? "Backend unreachable" : summary?.region ?? "Loading region…"}
          </span>
        </div>
      </div>

      <div className="hidden items-center gap-6 lg:flex">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium uppercase tracking-wide text-muted">System Status</span>
          {offline && <Badge tone="critical" dot>Offline</Badge>}
          {summary && <Badge tone={statusTone} dot>{summary.systemStatus}</Badge>}
        </div>
        <div className="h-5 w-px bg-border" />
        <div className="flex items-center gap-1.5 text-xs text-muted">
          <Clock className="h-3.5 w-3.5" strokeWidth={1.75} />
          Last plan: <span className="font-medium text-text">{summary ? formatTime(summary.lastPlanGeneratedAt) : "—"}</span>
        </div>
      </div>

      <div className="flex items-center gap-2.5 border-l border-border pl-3.5">
        <div className="hidden text-right leading-tight sm:block">
          <p className="text-xs font-semibold text-text">{coordinator?.name ?? "—"}</p>
          <p className="text-[11px] text-muted">{coordinator?.role ?? ""}</p>
        </div>
        <div className="flex h-9 w-9 flex-none items-center justify-center rounded-full bg-primary text-xs font-semibold text-background">
          {coordinator?.initials ?? "—"}
        </div>
      </div>
    </header>
  );
}
