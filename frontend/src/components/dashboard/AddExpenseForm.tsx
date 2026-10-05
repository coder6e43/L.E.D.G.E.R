import { useState, type FormEvent } from "react";
import { createExpense, type ExpenseInput } from "../../services/api";

const CATEGORIES = ["Food", "Travel", "Software", "Office Supplies", "Utilities", "Marketing", "Training", "Miscellaneous"];
export function AddExpenseForm({ onCreated }: { onCreated: () => void }) {
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [success, setSuccess] = useState("");
  const [form, setForm] = useState<ExpenseInput>({ category: "Food", amount: 0, currency: "INR", date: new Date().toISOString().slice(0, 10), description: "" });
  function change<K extends keyof ExpenseInput>(key: K, value: ExpenseInput[K]) { setForm((current) => ({ ...current, [key]: value })); }
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(""); setSuccess("");
    try { const record = await createExpense(form); setSuccess(`Expense ${record.expense_id} saved to ${record.cost_centre}.`); setForm((current) => ({ ...current, amount: 0, description: "" })); onCreated(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "The expense could not be saved."); } finally { setBusy(false); }
  }
  return <section className="panel add-expense-panel"><div className="panel-heading"><div><p className="section-kicker">Database-backed entry</p><h3>Add an expense</h3><small>The API assigns your identity and cost centre from your session.</small></div></div>
    <form className="expense-form" onSubmit={(event) => void submit(event)}>
      <label className="field"><span>Category</span><select value={form.category} onChange={(event) => change("category", event.target.value)}>{CATEGORIES.map((category) => <option key={category}>{category}</option>)}</select></label>
      <label className="field"><span>Amount</span><input type="number" min="0" step="0.01" required value={form.amount || ""} onChange={(event) => change("amount", Number(event.target.value))} /></label>
      <label className="field"><span>Currency</span><select value={form.currency} onChange={(event) => change("currency", event.target.value)}>{["INR", "USD", "EUR"].map((item) => <option key={item}>{item}</option>)}</select></label>
      <label className="field"><span>Date</span><input type="date" required value={form.date} onChange={(event) => change("date", event.target.value)} /></label>
      <label className="field expense-description"><span>Description</span><input maxLength={500} value={form.description} onChange={(event) => change("description", event.target.value)} placeholder="Optional details" /></label>
      <button className="primary expense-submit" type="submit" disabled={busy}>{busy ? "Saving…" : "Save expense"}</button>
    </form>
    {error && <p role="alert" className="login-error">{error}</p>}{success && <p role="status" className="expense-success">{success}</p>}
  </section>;
}
