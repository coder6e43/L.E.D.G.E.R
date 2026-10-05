import { Icon } from "../common/Icon";

export function SourceRowsTable({ sourceRows, queryId }: { sourceRows: string[]; queryId?: number | string }) {
  return <section className="panel source-panel">
    <div className="panel-heading"><div><p className="section-kicker">Evidence</p><h3>Source expense IDs</h3><small>{sourceRows.length} ID(s) returned by the backend</small></div></div>
    {sourceRows.length ? <div className="table-wrap"><table><thead><tr><th>Expense ID</th></tr></thead><tbody>{sourceRows.map((id) => <tr key={id}><td><strong>{id}</strong></td></tr>)}</tbody></table></div> : <p className="empty-evidence">No source rows matched these filters.</p>}
    <div className="table-footer"><span>Audit ID: {queryId ?? "Not supplied"}</span><span><Icon name="shield" size={15} /> Evidence returned by connected backend</span></div>
  </section>;
}
