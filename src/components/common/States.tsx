import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Loader2, Inbox, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface PanelStateProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  className?: string;
  action?: ReactNode;
}

function PanelState({ title, description, icon: Icon, className, action }: PanelStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 rounded-sm border border-dashed border-border px-6 py-10 text-center",
        className,
      )}
    >
      {Icon && <Icon className="h-6 w-6 text-muted" strokeWidth={1.5} />}
      <p className="text-sm font-medium text-text">{title}</p>
      {description && <p className="max-w-sm text-xs text-muted">{description}</p>}
      {action}
    </div>
  );
}

export function EmptyState({ title = "Nothing here yet", description, action, className }: Partial<PanelStateProps>) {
  return <PanelState title={title} description={description} icon={Inbox} action={action} className={className} />;
}

export function ErrorState({ title = "Could not load data", description, action, className }: Partial<PanelStateProps>) {
  return (
    <PanelState
      title={title}
      description={description}
      icon={AlertTriangle}
      action={action}
      className={cn("border-critical/30", className)}
    />
  );
}

export function LoadingState({ title = "Loading…", className }: { title?: string; className?: string }) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-2 px-6 py-10 text-center", className)}>
      <Loader2 className="h-5 w-5 animate-spin text-secondary" strokeWidth={1.75} />
      <p className="text-xs text-muted">{title}</p>
    </div>
  );
}
