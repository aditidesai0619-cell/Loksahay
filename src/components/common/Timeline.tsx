import type { TrackingEvent } from "@/types";
import { formatTime, cn } from "@/lib/utils";

export function Timeline({ events }: { events: TrackingEvent[] }) {
  return (
    <ol className="flex flex-col">
      {events.map((event, i) => {
        const isLast = i === events.length - 1;
        return (
          <li key={event.id} className="relative flex gap-3 pb-5 last:pb-0">
            {!isLast && (
              <span className="absolute left-[5px] top-3 h-full w-px bg-border" aria-hidden />
            )}
            <span
              className={cn(
                "relative mt-1 h-[11px] w-[11px] flex-none rounded-full border-2",
                isLast ? "border-primary bg-primary" : "border-secondary bg-surface",
              )}
            />
            <div className="flex-1 pb-0.5">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-text">{event.status}</span>
                <span className="text-[11px] text-muted tabular">{formatTime(event.timestamp)}</span>
              </div>
              {event.note && <p className="mt-0.5 text-xs text-muted">{event.note}</p>}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
