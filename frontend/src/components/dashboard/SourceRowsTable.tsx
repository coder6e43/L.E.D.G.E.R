import { Icon } from "../common/Icon";
import { Button } from "../common/Button";
import { workspaceTransactions } from "../../data/mockData";
import type { Transaction } from "../../types";

export function SourceRowsTable() {
  return (
    <section className="panel source-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Evidence</p>
          <h3>Source transactions</h3>
          <small>37 transactions contributed to this result</small>
        </div>

        <Button className="secondary">
          View all 37 <Icon name="arrow" size={16} />
        </Button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Category</th>
              <th>Amount</th>
            </tr>
          </thead>

          <tbody>
            {workspaceTransactions.map((row: Transaction) => (
              <tr key={row.id}>
                <td>{row.date}</td>

                <td>
                  <strong>{row.merchant}</strong>
                  <small>
                    {row.method} · {row.note}
                  </small>
                </td>

                <td>
                  <span className="category-pill">
                    <span /> {row.category}
                  </span>
                </td>

                <td>
                  {row.amount < 0 ? "−" : "+"}₹
                  {Math.abs(row.amount).toLocaleString("en-IN")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="table-footer">
        <span>Showing 6 of 37 source transactions</span>
        <span>
          <Icon name="shield" size={15} /> Evidence supplied by connected
          backend
        </span>
      </div>
    </section>
  );
}