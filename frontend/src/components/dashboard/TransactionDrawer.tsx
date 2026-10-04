import { useState } from "react";
import { Button } from "../common/Button";
import { Icon } from "../common/Icon";
import { formatMoney } from "../../utils/formatters";
import type { Transaction } from "../../types";

export function TransactionDrawer({ transaction, onClose }: { transaction: Transaction; onClose: () => void }) {
  const [reviewed, setReviewed] = useState(false);
  const [editingCategory, setEditingCategory] = useState(false);
  const [addingNote, setAddingNote] = useState(false);
  return (
    <div className="drawer-layer" role="dialog" aria-modal="true" aria-label="Transaction details">
      <button className="drawer-backdrop" onClick={onClose} aria-label="Close transaction details" />
      <aside className="transaction-drawer">
        <div className="drawer-header"><div><p className="section-kicker">Transaction detail</p><h2>{transaction.merchant}</h2></div><Button className="icon-button" onClick={onClose}><Icon name="x" size={20} /><span className="sr-only">Close</span></Button></div>
        <div className={`drawer-amount ${transaction.type === "income" ? "income" : ""}`}><span>{transaction.type === "income" ? "Money received" : "Amount paid"}</span><strong>{transaction.type === "income" ? "+" : ""}{formatMoney(transaction.amount)}</strong><small className={`status status-${transaction.status.toLowerCase()}`}>{transaction.status}</small></div>
        <dl className="detail-list">
          <div><dt>Date and time</dt><dd>{transaction.date} · {transaction.time}</dd></div>
          <div><dt>Category</dt><dd>{editingCategory ? <select defaultValue={transaction.category}><option>{transaction.category}</option><option>Food</option><option>Shopping</option><option>Utilities</option></select> : transaction.category}</dd></div>
          <div><dt>Account</dt><dd>{transaction.account}</dd></div>
          <div><dt>Payment method</dt><dd>{transaction.method}</dd></div>
          <div><dt>Transaction ID</dt><dd><code>{transaction.id}</code></dd></div>
          <div><dt>Notes</dt><dd>{addingNote ? <textarea defaultValue={transaction.note} aria-label="Transaction note" /> : transaction.note}</dd></div>
        </dl>
        <div className="timeline"><p>Transaction timeline</p>{["Initiated", "Processing", transaction.status].map((step, index) => <div key={step} className={transaction.status === "Failed" && index === 2 ? "failed" : transaction.status === "Pending" && index === 2 ? "pending" : "complete"}><span><Icon name={index === 2 && transaction.status === "Failed" ? "x" : "check"} size={12} /></span><strong>{step}</strong><small>{index === 0 ? transaction.time : index === 1 ? "A few moments later" : transaction.status === "Pending" ? "In progress" : "Confirmed"}</small></div>)}</div>
        <div className="drawer-actions"><Button onClick={() => setEditingCategory(!editingCategory)}>Edit category</Button><Button onClick={() => setAddingNote(!addingNote)}>Add note</Button><Button className={reviewed ? "reviewed" : "primary"} onClick={() => setReviewed(!reviewed)}><Icon name="check" size={16} /> {reviewed ? "Reviewed" : "Mark as reviewed"}</Button></div>
      </aside>
    </div>
  );
}
