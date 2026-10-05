import { Icon } from "../common/Icon";
import type { QueryResult } from "../../services/api";

export function ResultCard({ prompt, result }: { prompt: string; result: QueryResult }) {
  const empty = (result.row_count ?? result.source_rows.length) === 0 && result.formula !== "COUNT(*)";
  return <section className="result-card">
    <div className="result-top"><div><p className="result-label"><span><Icon name={empty ? "info" : "check"} size={14} /></span>{empty ? "No matching records" : "Financial result"}</p><p className="answered-query">{prompt}</p></div>
      <span className="result-status"><Icon name="shield" size={15} /> Authenticated data scope</span></div>
    <div className="result-main"><div className="answer"><span>{empty ? "Matching expenses" : result.formula === "COUNT(*)" ? "Expense count" : "Calculated result"}</span>
      <strong>{empty ? "No matches" : formatValue(result.result, result.currency, result.formula)}</strong>
      <small>{empty ? "No records matched the requested filters in your authorized scope." : `${result.row_count ?? result.source_rows.length} source row(s) · ${result.formula ?? "Calculation"}`}</small></div>
      <div className="result-divider" /><div className="answer-context">
        <div><span className="context-icon"><Icon name="receipt" size={19} /></span><span><small>Evidence rows</small><strong>{result.row_count ?? result.source_rows.length}</strong></span></div>
        <div><span className="context-icon"><Icon name="shield" size={19} /></span><span><small>Audit reference</small><strong>{result.query_id ?? "Unavailable"}</strong></span></div>
      </div>
    </div>
  </section>;
}

export function formatValue(value: unknown, currency: string | null, formula?: string) {
  if (typeof value === "number") {
    if (formula === "COUNT(*)") return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(value);
    if (currency) return new Intl.NumberFormat("en-IN", { style: "currency", currency }).format(value);
    return new Intl.NumberFormat("en-IN").format(value);
  }
  if (Array.isArray(value)) return `${value.length} matching record(s)`;
  return value == null ? "No result" : typeof value === "object" ? JSON.stringify(value) : String(value);
}
