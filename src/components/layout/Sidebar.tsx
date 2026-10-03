import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ClipboardList,
  Boxes,
  Workflow,
  Map as MapIcon,
  Truck,
  RefreshCcw,
  FlaskConical,
  BarChart3,
  Activity,
  UserCircle2,
  Settings,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Logo } from "@/components/common/Logo";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/needs", label: "Needs", icon: ClipboardList },
  { to: "/resources", label: "Resources", icon: Boxes },
  { to: "/allocation", label: "Allocation", icon: Workflow },
  { to: "/map", label: "Relief Map", icon: MapIcon },
  { to: "/transport", label: "Transport", icon: Truck },
  { to: "/replanning", label: "Replanning", icon: RefreshCcw },
  { to: "/simulator", label: "Scenario Simulator", icon: FlaskConical },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

const FOOTER_ITEMS = [
  { to: "/system-status", label: "System Status", icon: Activity },
  { to: "/profile", label: "Coordinator Profile", icon: UserCircle2 },
  { to: "/settings", label: "Settings", icon: Settings },
];

interface SidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

function Brand() {
  return (
    <div className="flex items-center gap-2.5 px-4 py-4">
      <div className="flex h-9 w-9 flex-none items-center justify-center rounded-md bg-background/95 shadow-card">
        <Logo size={26} />
      </div>
      <div className="leading-tight">
        <p className="text-sm font-bold tracking-tight text-background">LOKSAHAY</p>
        <p className="text-[10px] uppercase tracking-wide text-background/55">Relief Operations</p>
      </div>
    </div>
  );
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-1 flex-col gap-0.5 px-2.5">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          onClick={onNavigate}
          end={item.to === "/"}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-2.5 rounded-md border-l-2 px-2.5 py-2 text-sm transition-colors",
              isActive
                ? "border-accent bg-white/10 font-medium text-background"
                : "border-transparent text-background/65 hover:bg-white/5 hover:text-background",
            )
          }
        >
          <item.icon className="h-[17px] w-[17px] flex-none" strokeWidth={1.75} />
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

function FooterList({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex flex-col gap-0.5 border-t border-white/10 px-2.5 pt-2.5">
      {FOOTER_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-2.5 rounded-md border-l-2 px-2.5 py-2 text-sm transition-colors",
              isActive
                ? "border-accent bg-white/10 font-medium text-background"
                : "border-transparent text-background/65 hover:bg-white/5 hover:text-background",
            )
          }
        >
          <item.icon className="h-[17px] w-[17px] flex-none" strokeWidth={1.75} />
          {item.label}
        </NavLink>
      ))}
    </div>
  );
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  return (
    <>
      <aside className="hidden w-[232px] flex-none flex-col bg-primary md:flex">
        <Brand />
        <NavList />
        <FooterList />
        <div className="h-3" />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <div className="absolute inset-0 bg-text/30" onClick={onMobileClose} />
          <div className="relative flex h-full w-[260px] flex-col bg-primary shadow-2xl">
            <div className="flex items-center justify-between">
              <Brand />
              <button onClick={onMobileClose} className="mr-3 rounded-md p-1.5 text-background/70 hover:bg-white/10 hover:text-background">
                <X className="h-4 w-4" strokeWidth={1.75} />
              </button>
            </div>
            <NavList onNavigate={onMobileClose} />
            <FooterList onNavigate={onMobileClose} />
            <div className="h-3" />
          </div>
        </div>
      )}
    </>
  );
}
