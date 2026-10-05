import { useEffect, useState } from "react";
import { Brand } from "./components/common/Brand";
import { Login } from "./components/auth/Login";
import { currentUser, executeQuery, login, logout, type LedgerUser, type QueryResult } from "./services/api";
import "./ledger.css";

// Compatibility export for the inactive prototype landing components.
export function useTheme() { return { theme: "light" as "light" | "dark", toggleTheme: () => undefined }; }

export default function App() {
  const [user, setUser] = useState<LedgerUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { currentUser().then(setUser).catch(() => setUser(null)).finally(() => setChecking(false)); }, []);

  async function ask(question = prompt) {
    if (!question.trim()) return;
    setPrompt(question);
    setError("");
    setBusy(true);
    try { setResult(await executeQuery(question)); }
    catch (e) { setResult(null); setError(e instanceof Error ? e.message : "The query could not be completed."); }
    finally { setBusy(false); }
  }

  async function signOut() { await logout(); setUser(null); setResult(null); setPrompt(""); }

  if (checking) return <main className="ledger-wait">Loading secure workspace…</main>;
  if (!user) return <Login onLogin={async (email, password) => { try { setUser(await login(email, password)); return true; } catch { return false; } }} />;
  const examples = user.role === "Employee"
    ? ["How many expenses did I submit in 2026?", "How much did I spend on Travel this year?", "Show my top 5 expenses this month."]
    : ["How much did we spend on Food in September 2026?", "Show our top 5 Travel expenses this month.", "How many Food expenses did we submit this month?"];

  return <div className="ledger-app">
    <header className="ledger-header"><Brand /><div className="ledger-identity"><span>{user.name}</span><small>{user.role} · {user.cost_centre}</small><button onClick={signOut}>Sign out</button></div></header>
    <main className="ledger-main">
      <p className="ledger-kicker">L.E.D.G.E.R. · Evidence-backed finance</p>
      <h1>Ask your financial data.</h1>
      <p className="ledger-subtitle">Answers are calculated from authorized database records and linked to their source rows.</p>
      <form className="ledger-query" onSubmit={(e) => { e.preventDefault(); void ask(); }}>
        <label htmlFor="prompt">What would you like to know?</label>
        <textarea id="prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="How much did I spend on Food this month?" rows={3} />
        <button disabled={busy || !prompt.trim()}>{busy ? "Calculating…" : "Ask LEDGER"}</button>
      </form>
      <div className="ledger-examples"><span>Try:</span>{examples.map((x) => <button key={x} onClick={() => void ask(x)} disabled={busy}>{x}</button>)}</div>
      {error && <p className="ledger-error" role="alert">{error}</p>}
      {result && <section className="ledger-result" aria-live="polite">
        <div className="ledger-result-head"><div><p className="ledger-kicker">{result.status === "SUCCESS" ? "Verified result" : result.status}</p><h2>{result.status === "SUCCESS" ? formatResult(result.result, result.currency, result.formula) : result.message || result.error || "The query needs clarification."}</h2></div><span>{result.query_id ? `Audit ${result.query_id}` : ""}</span></div>
        {result.status === "SUCCESS" && <>
          <p className="ledger-meta">{result.formula || "Calculation"} · {result.row_count ?? result.source_rows.length} source row(s)</p>
          {result.source_rows.length > 0 && <details open><summary>Evidence · {result.source_rows.length} authorized source row ID(s)</summary><div className="ledger-table-wrap"><table><thead><tr><th>Expense ID</th></tr></thead><tbody>{result.source_rows.map((row) => <tr key={row}><td>{row}</td></tr>)}</tbody></table></div></details>}
          {result.source_rows.length === 0 && <p className="ledger-meta">No matching source rows.</p>}
        </>}
      </section>}
      <p className="ledger-scope-note">Your role and data scope come from your authenticated account. Request-supplied identity and scope fields are rejected.</p>
    </main>
  </div>;
}

function formatResult(value: unknown, currency: string | null, formula?: string): string {
  if (typeof value === "number") {
    if (formula === "COUNT(*)") return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(value);
    return currency ? new Intl.NumberFormat("en-IN", { style: "currency", currency }).format(value) : new Intl.NumberFormat("en-IN").format(value);
  }
  if (Array.isArray(value)) return `${value.length} matching record(s)`;
  return typeof value === "object" && value ? JSON.stringify(value) : String(value ?? "No result");
}
