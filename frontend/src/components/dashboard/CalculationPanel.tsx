import { Icon } from "../common/Icon";
import type { QueryResult } from "../../services/api";
import { formatValue } from "./ResultCard";

export function CalculationPanel({ result }: { result: QueryResult }) {
  const count = result.row_count ?? result.source_rows.length;
  const empty = count === 0 && result.formula !== "COUNT(*)";
  return <section className="panel calculation-panel">
    <div className="panel-heading"><div><p className="section-kicker">Method</p><h3>Calculation details</h3></div><span className="verified"><Icon name="check" size={14} /> Backend result</span></div>
    <div className="formula"><span>Formula reported by calculation engine</span><code>{result.formula ?? "Not provided"}</code></div>
    <div className="calc-flow"><div><span>01</span><p>Authorized source rows<strong>{count} records</strong></p></div><Icon name="chevron" size={17} /><div><span>02</span><p>Calculation<strong>{result.formula ?? "As reported"}</strong></p></div><Icon name="chevron" size={17} /><div className="calc-total"><span>03</span><p>Result<strong>{empty ? "No matching records" : formatValue(result.result, result.currency, result.formula)}</strong></p></div></div>
    <details><summary>Evidence reference <Icon name="chevron" size={16} /></summary><p>Audit ID: {result.query_id ?? "Not supplied"}. Source IDs below are the exact identifiers returned by the backend.</p></details>
  </section>;
}
