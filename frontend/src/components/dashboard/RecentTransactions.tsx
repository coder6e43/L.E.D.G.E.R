import { Button } from "../common/Button";
import { Icon } from "../common/Icon";
import { formatMoney } from "../../utils/formatters";
import type { DrillFilter, Transaction } from "../../types";

export function RecentTransactions({
  rows,
  filter,
  onClear,
  onOpen,
}: {
  rows: Transaction[];
  filter: DrillFilter;
  onClear: () => void;
  onOpen: (transaction: Transaction) => void;
}) {
  const title = filter === "all" ? "Recent transactions" : filter === "savings" ? "Savings calculation transactions" : `${filter.charAt(0).toUpperCase()}${filter.slice(1)} transactions`;
  return (
    <section className="panel transactions-panel">
      <div className="panel-heading">
        <div><p className="section-kicker">Source activity</p><h3>{title}</h3><small>{rows.length} recent records in the current account scope</small></div>
        {filter !== "all" && <Button className="secondary" onClick={onClear}><Icon name="x" size={15} /> Clear filter</Button>}
      </div>
      {filter === "savings" && <div className="calculation-strip"><Icon name="info" size={16} /><span><strong>Savings = income − expenses</strong>Both incoming and outgoing transactions are included below.</span></div>}
      <div className="table-wrap transaction-table">
        <table>
          <thead><tr><th>Merchant</th><th>Category</th><th>Account</th><th>Date</th><th>Status</th><th>Amount</th></tr></thead>
          <tbody>{rows.map((row) => <tr key={row.id} tabIndex={0} onClick={() => onOpen(row)} onKeyDown={(event) => { if (event.key === "Enter") onOpen(row); }}>
            <td><strong>{row.merchant}</strong><small>{row.id}</small></td><td>{row.category}</td><td>{row.account}</td><td>{row.date}</td><td><span className={`status status-${row.status.toLowerCase()}`}>{row.status}</span></td><td className={row.type === "income" ? "amount-positive" : ""}>{row.type === "income" ? "+" : ""}{formatMoney(row.amount)}</td>
          </tr>)}</tbody>
        </table>
      </div>
      <div className="table-footer"><span>Click any row to view transaction details</span><span><Icon name="shield" size={15} /> Fictional prototype records</span></div>
    </section>
  );
}
