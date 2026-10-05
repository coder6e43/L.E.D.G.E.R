import { useEffect, useState } from "react";
import { Login } from "./components/auth/Login";
import { Header } from "./components/dashboard/Header";
import { QueryBox } from "./components/dashboard/QueryBox";
import { ResultCard } from "./components/dashboard/ResultCard";
import { ContextPanel } from "./components/dashboard/ContextPanel";
import { CalculationPanel } from "./components/dashboard/CalculationPanel";
import { SourceRowsTable } from "./components/dashboard/SourceRowsTable";
import { currentUser, executeQuery, login, logout, type LedgerUser, type QueryResult } from "./services/api";
import "./index.css";

export function useTheme() { return { theme: "light" as "light" | "dark", toggleTheme: () => undefined }; }

export default function App() {
  const [user, setUser] = useState<LedgerUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => { currentUser().then(setUser).catch(() => setUser(null)).finally(() => setChecking(false)); }, []);

  async function ask(question = prompt) {
    if (!question.trim() || busy) return;
    setPrompt(question);
    setError("");
    setResult(null);
    setBusy(true);
    try { setResult(await executeQuery(question)); }
    catch (cause) {
      setError(cause instanceof Error ? cause.message : "The query could not be completed.");
    } finally { setBusy(false); }
  }

  async function signOut() {
    try { await logout(); } finally { setUser(null); setResult(null); setPrompt(""); }
  }

  if (checking) return <main className="dashboard" aria-live="polite">Loading secure workspace…</main>;
  if (!user) return <Login onLogin={async (email, password) => {
    try { setUser(await login(email, password)); return true; }
    catch { return false; }
  }} />;

  const examples = user.role === "Employee"
    ? ["How many expenses did I submit in 2026?", "How much did I spend on Travel in August 2026?", "Show my Travel transactions this month."]
    : user.role === "Manager"
      ? ["How much did we spend on Food in September 2026?", "How much did we spend on Travel in September 2026?", "Show our top 3 Travel expenses this month."]
      : ["How much did the organization spend on Food in September 2026?", "How much did we spend on Travel in September 2026?", "How many expenses did the organization submit in 2026?"];

  return <div className="app-shell" data-theme={theme}>
    <Header user={user} onLogout={() => void signOut()} theme={theme} onTheme={() => setTheme((current) => current === "light" ? "dark" : "light")} />
    <main className="dashboard">
      <section className="welcome">
        <div><p className="section-kicker">L.E.D.G.E.R. · Evidence-backed finance</p><h1>Ask your financial data.</h1><p>Results are calculated from database records within your authenticated access scope.</p></div>
        <div className="workspace-status"><span className="status-dot" /> Connected to the secure workspace</div>
      </section>
      <QueryBox query={prompt} setQuery={setPrompt} submit={() => void ask()} loading={busy} examples={examples} />
      {busy && <section className="panel" aria-live="polite" style={{ padding: 24, marginTop: 20 }}>Compiling your question and calculating from authorized records…</section>}
      {error && <section className="state-card state-error" role="alert" style={{ marginTop: 20 }}><div className="state-content"><p className="state-eyebrow">Request failed</p><h3>Unable to complete the query</h3><p>{error}</p></div></section>}
      {result && <section className="analytics-workspace" aria-live="polite">
        {result.status === "SUCCESS" ? <>
          <ResultCard prompt={prompt} result={result} />
          <ContextPanel filters={result.filters ?? {}} user={user} />
          <CalculationPanel result={result} />
          <SourceRowsTable sourceRows={result.source_rows ?? []} queryId={result.query_id} />
        </> : <section className={`state-card state-${result.status.toLowerCase()}`}>
          <div className="state-content"><p className="state-eyebrow">{result.status === "REFUSED" ? "Unable to answer" : result.status === "ACCESS_DENIED" ? "Access denied" : "Query needs attention"}</p>
            <h3>{result.message || result.error || "The query could not be completed."}</h3>
            {result.query_id && <p>Audit reference: {result.query_id}</p>}
          </div>
        </section>}
      </section>}
      <p className="prototype-note">Identity and data scope are supplied by the authenticated backend session. The browser sends only your question.</p>
    </main>
  </div>;
}
