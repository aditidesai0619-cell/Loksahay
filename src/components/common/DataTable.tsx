import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { EmptyState } from "./States";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  align?: "left" | "right" | "center";
  widthClassName?: string;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
  emptyTitle?: string;
  emptyDescription?: string;
}

export function DataTable<T>({ columns, rows, rowKey, onRowClick, emptyTitle, emptyDescription }: DataTableProps<T>) {
  if (rows.length === 0) {
    return <EmptyState title={emptyTitle ?? "No records match"} description={emptyDescription} />;
  }

  return (
    <div className="overflow-x-auto rounded-sm border border-border bg-surface shadow-card">
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <thead>
          <tr className="sticky top-0 z-10 border-b border-border bg-surface-sunken">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  "px-3.5 py-3 text-[11px] font-semibold uppercase tracking-wide text-muted",
                  col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left",
                  col.widthClassName,
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={cn(
                "border-b border-border last:border-0",
                onRowClick && "cursor-pointer hover:bg-surface-sunken",
              )}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={cn(
                    "px-3.5 py-3 align-middle text-text",
                    col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left",
                  )}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
