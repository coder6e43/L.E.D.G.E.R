import { Icon } from "../common/Icon";
import type { LedgerUser } from "../../services/api";

export function ContextPanel({ filters, user }: { filters: Record<string, unknown>; user: LedgerUser }) {
  const entries = Object.entries(filters).filter(([, value]) => value !== null && value !== undefined && value !== "");
  const scope = `${user.role} · ${user.cost_centre}`;
  return <section className="panel context-panel">
    <div className="panel-heading"><div><p className="section-kicker">Query context</p><h3>Scope and filters</h3></div><Icon name="info" size={19} /></div>
    <div className="metadata-grid">
      <div><span>Authenticated scope</span><strong>{scope}</strong></div>
      {entries.map(([key, value]) => <div key={key}><span>{humanize(key)}</span><strong>{formatContext(key, value)}</strong></div>)}
    </div>
    {entries.length > 0 && <div className="filters"><span>Filters applied</span>{entries.map(([key, value]) => <b key={key}>{humanize(key)}: {formatContext(key, value)}</b>)}</div>}
  </section>;
}

function humanize(value: string) { return value.replace(/_/g, " ").replace(/\b\w/g, (letter: string) => letter.toUpperCase()); }
function formatContext(key: string, value: unknown) {
  if (key === "scope" && value && typeof value === "object") {
    const scope = value as Record<string, unknown>;
    if (scope.scope_type === "user") return `User ${String(scope.scope_user_id ?? "")}`;
    if (scope.scope_type === "cost_centre") return `Cost centre ${String(scope.cost_centre ?? "")}`;
    if (scope.scope_type === "organization") return "Organization";
  }
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}
