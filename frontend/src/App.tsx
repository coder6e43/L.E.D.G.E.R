import { useCallback, useEffect, useState } from "react";
import { BrowserRouter, Navigate, useLocation, useNavigate } from "react-router";
import { Login } from "./components/auth/Login";
import { Header } from "./components/dashboard/Header";
import { QueryBox } from "./components/dashboard/QueryBox";
import { FilterBar } from "./components/dashboard/FilterBar";
import { ResultCard } from "./components/dashboard/ResultCard";
import { ContextPanel } from "./components/dashboard/ContextPanel";
import { CalculationPanel } from "./components/dashboard/CalculationPanel";
import { SourceRowsTable } from "./components/dashboard/SourceRowsTable";
import { AnalyticsOverview } from "./components/dashboard/AnalyticsOverview";
import { AddExpenseForm } from "./components/dashboard/AddExpenseForm";
import { AdminPortal } from "./components/admin/AdminPortal";
import { currentUser, executeQuery, getAnalyticsOverview, googleStatus, login, logout, startGoogleLogin, type AnalyticsOverview as Overview, type LedgerUser, type QueryResult } from "./services/api";
import "./index.css";

export function useTheme() { return { theme: "light" as "light" | "dark", toggleTheme: () => undefined }; }

export default function App() {
  return <BrowserRouter><SessionApp /></BrowserRouter>;
}

function SessionApp() {
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState<LedgerUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [analytics, setAnalytics] = useState<Overview | null>(null);
  const [analyticsError, setAnalyticsError] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">("light");

  const refreshIdentity = useCallback(async () => { setUser(await currentUser()); }, []);
  const refreshAnalytics = useCallback(async () => {
    try { setAnalytics(await getAnalyticsOverview()); setAnalyticsError(""); }
    catch (cause) { setAnalyticsError(cause instanceof Error ? cause.message : "Analytics could not be loaded."); }
  }, []);

  useEffect(() => {
    currentUser().then(setUser).catch(() => setUser(null)).finally(() => setChecking(false));
    googleStatus().then((status) => setGoogleEnabled(status.enabled)).catch(() => setGoogleEnabled(false));
  }, []);
  useEffect(() => {
    if (user && location.pathname === "/analytics") void refreshAnalytics();
  }, [user, location.pathname, refreshAnalytics]);

  function hasExplicitDateContext(question: string): boolean {
  const text = question.toLowerCase();

  return (
    /\b20\d{2}\b/.test(text) ||
    /\b(today|yesterday|this week|last week|this month|last month|this quarter|last quarter|year to date|ytd)\b/.test(text) ||
    /\b(january|february|march|april|may|june|july|august|september|october|november|december)\b/.test(text) ||
    /\b\d{4}-\d{2}-\d{2}\b/.test(text) ||
    /\b\d{1,2}\/\d{1,2}\/\d{4}\b/.test(text)
  );
}

  async function ask(question = prompt) {
  if (!question.trim() || busy) return;

  setPrompt(question);
  setError("");
  setResult(null);
  setBusy(true);

  const queryWithDateRange =
    startDate &&
    endDate &&
    !hasExplicitDateContext(question)
      ? `${question} between ${startDate} and ${endDate}`
      : question;

  try {
    setResult(await executeQuery(queryWithDateRange));

    if (location.pathname === "/analytics") {
      navigate("/");
    }
  } catch (cause) {
    setError(
      cause instanceof Error
        ? cause.message
        : "The query could not be completed.",
    );
  } finally {
    setBusy(false);
  }
}

  async function signOut() {
    try { await logout(); }
    finally { setUser(null); setResult(null); setPrompt(""); navigate("/"); }
  }

  if (checking) return <main className="dashboard" aria-live="polite">Loading secure workspace…</main>;
  if (!user) return <Login googleEnabled={googleEnabled} onGoogle={startGoogleLogin} onLogin={async (email, password) => {
    try { setUser(await login(email, password)); return true; }
    catch { return false; }
  }} />;

  const header = <Header user={user} onLogout={() => void signOut()} theme={theme} onTheme={() => setTheme((current) => current === "light" ? "dark" : "light")} />;
  if (location.pathname === "/admin") {
    if (user.role !== "Admin") return <Navigate to="/" replace />;
    return <div className="app-shell" data-theme={theme}>{header}<AdminPortal onIdentityChanged={refreshIdentity} /></div>;
  }
  if (location.pathname === "/analytics") {
    return <div className="app-shell" data-theme={theme}>{header}<main className="dashboard analytics-page">
      <section className="welcome"><div><p className="section-kicker">L.E.D.G.E.R. · Evidence-backed finance</p><h1>Spending analytics.</h1><p>Monthly and category totals from records within your authenticated data scope.</p></div><div className="workspace-status"><span className="status-dot" /> Connected to the secure workspace</div></section>
      {analytics && <AnalyticsOverview data={analytics} onAsk={(question) => void ask(question)} />}
      {analyticsError && <section className="state-card state-error" role="alert"><div className="state-content"><p className="state-eyebrow">Analytics unavailable</p><p>{analyticsError}</p></div></section>}
    </main></div>;
  }
  if (location.pathname === "/expenses/new") {
    return <div className="app-shell" data-theme={theme}>{header}<main className="dashboard expense-page">
      <section className="welcome"><div><p className="section-kicker">L.E.D.G.E.R. · Expense entry</p><h1>Add an expense.</h1><p>The API assigns your identity and cost centre from your authenticated session.</p></div><div className="workspace-status"><span className="status-dot" /> Connected to the secure workspace</div></section>
      <AddExpenseForm onCreated={() => void refreshAnalytics()} />
    </main></div>;
  }

  const examples = user.role === "Employee"
    ? ["How many expenses did I submit in 2026?", "How much did I spend on Travel in August 2026?", "Show my Travel transactions this month."]
    : user.role === "Manager"
      ? ["How much did we spend on Food in September 2026?", "How much did we spend on Travel in September 2026?", "Show our top 3 Travel expenses this month."]
      : ["How much did the organization spend on Food in September 2026?", "How much did we spend on Travel in September 2026?", "How many expenses did the organization submit in 2026?"];

  return <div className="app-shell" data-theme={theme}>
    {header}
    <main className="dashboard">
      <section className="welcome">
        <div><p className="section-kicker">L.E.D.G.E.R. · Evidence-backed finance</p><h1>Ask your financial data.</h1><p>Results are calculated from database records within your authenticated access scope.</p></div>
        <div className="workspace-status"><span className="status-dot" /> Connected to the secure workspace</div>
      </section>
      <FilterBar
  onDateRangeChange={(start, end) => {
    setStartDate(start);
    setEndDate(end);
  }}
/>
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
