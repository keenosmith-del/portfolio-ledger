import type { ReactNode } from "react";
import { FileText, ChevronLeft, ChevronRight } from "lucide-react";
const readable = (value: string) => value.replaceAll("_", " ");
export function Badge({ value }: { value: string }) {
  return (
    <span
      className={`badge ${["completed", "accepted", "resolved", "active", "ready", "eligible"].includes(value) ? "good" : ["quarantined", "failed", "high", "open", "partially_completed", "stale"].includes(value) ? "warn" : ""}`}
    >
      <span />
      {readable(value)}
    </span>
  );
}
export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="empty">
      <FileText size={28} />
      <p>{children}</p>
    </div>
  );
}
export function Table<T extends { id: string }>({
  rows,
  columns,
  onClick,
}: {
  rows: T[];
  columns: { label: string; render: (row: T) => ReactNode }[];
  onClick?: (row: T) => void;
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.label}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              {columns.map((c, i) => (
                <td key={c.label}>
                  {i === 0 && onClick ? (
                    <button
                      className="text-button"
                      onClick={() => onClick(row)}
                    >
                      {c.render(row)}
                    </button>
                  ) : (
                    c.render(row)
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <Empty>No records match this view.</Empty>}
    </div>
  );
}
export function Pager({
  offset,
  total,
  onChange,
}: {
  offset: number;
  total: number;
  onChange: (n: number) => void;
}) {
  return (
    <div className="pager">
      <span>
        {total
          ? `${offset + 1}–${Math.min(offset + 25, total)} of ${total}`
          : "0 records"}
      </span>
      <div>
        <button
          className="icon-button"
          aria-label="Previous page"
          disabled={offset === 0}
          onClick={() => onChange(Math.max(0, offset - 25))}
        >
          <ChevronLeft size={16} />
        </button>
        <button
          className="icon-button"
          aria-label="Next page"
          disabled={offset + 25 >= total}
          onClick={() => onChange(offset + 25)}
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
export function Panel({
  title,
  subtitle,
  children,
  action,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
