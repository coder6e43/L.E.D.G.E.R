import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { createBrowserRouter, RouterProvider, useNavigate } from "react-router";

import { Icon } from "./components/common/Icon";
import type { IconName } from "./components/common/Icon";
import { Button } from "./components/common/Button";
import { Brand } from "./components/common/Brand";
import { Login } from "./components/auth/Login";
import { LandingHeader } from "./components/landing/LandingHeader";
import { LandingDashboardPreview } from "./components/landing/LandingDashboardPreview";
import { Header } from "./components/dashboard/Header";
import { SummaryCard } from "./components/dashboard/SummaryCard";
import { QueryBox } from "./components/dashboard/QueryBox";
import { LoadingState } from "./components/dashboard/LoadingState";
import { StatusState } from "./components/dashboard/StatusState";
import { ResultCard } from "./components/dashboard/ResultCard";
import { ContextPanel } from "./components/dashboard/ContextPanel";
import { CalculationPanel } from "./components/dashboard/CalculationPanel";
import { ChartPanel } from "./components/dashboard/ChartPanel";
import { SourceRowsTable } from "./components/dashboard/SourceRowsTable";
import { FilterBar } from "./components/dashboard/FilterBar";
import { CashFlowChart } from "./components/dashboard/CashFlowChart";
import { IncomeExpensePanel } from "./components/dashboard/IncomeExpensePanel";
import { SpendingCategories } from "./components/dashboard/SpendingCategories";
import { FinancialInsights } from "./components/dashboard/FinancialInsights";
import { RecentTransactions } from "./components/dashboard/RecentTransactions";
import { TransactionDrawer } from "./components/dashboard/TransactionDrawer";

import AdminPortal from "./components/admin/AdminPortal";

import { accountFactors, categoryBase, examples, periodData, workspaceTransactions } from "./data/mockData";
import { formatMoney, percentChange } from "./utils/formatters";
import type { AccountKey, Analytics, CategoryDatum, DrillFilter, PeriodKey, ResultState, Theme, Transaction } from "./types";

const ThemeContext = createContext<{ theme: Theme; toggleTheme: () => void }>({
  theme: "light",
  toggleTheme: () => undefined,
});

export function useTheme() {
  return useContext(ThemeContext);
}

const landingFeatures = [
  { icon: "search" as IconName, title: "Ask Questions", text: "Ask questions about your finances in natural language and get clear answers." },
  { icon: "shield" as IconName, title: "Secure Data", text: "Your financial information is protected with security-focused architecture." },
  { icon: "chart" as IconName, title: "Understand Results", text: "Turn complex financial information into simple, understandable insights." },
  { icon: "check" as IconName, title: "Trusted Insights", text: "Get transparent answers backed by your financial data." },
];

function LandingPage() {
  const navigate = useNavigate();
  const governance = [
    ["Role-Based Access", "Give people access only to the financial information they need.", "user"],
    ["Data Privacy", "Keep sensitive financial data protected throughout every interaction.", "shield"],
    ["Transparent Logic", "Understand the rules and calculations behind every result.", "info"],
    ["Auditability", "Trace insights back to their supporting transactions and context.", "receipt"],
    ["Data Minimization", "Use only the information required to answer each question.", "budget"],
    ["Explainable Insights", "See clear context instead of unexplained generated numbers.", "spark"],
  ] as const;
  return (
    <div className="landing-page">
      <LandingHeader />
      <main>
        <section className="landing-hero" id="home">
          <div className="hero-copy">
            <p className="landing-eyebrow"><span /> Transparent financial intelligence</p>
            <h1>Ask Your Financial Data.<br /><em>Get Answers You Can Trust.</em></h1>
            <p className="hero-description">Ledger turns your financial data into clear, actionable insights so you can understand where your money goes and make better decisions.</p>
            <div className="hero-actions"><Button className="primary landing-primary" onClick={() => navigate("/signup")}>Get Started <Icon name="arrow" size={18} /></Button><Button className="landing-secondary" onClick={() => navigate("/login")}>Log In</Button></div>
            <div className="hero-proof"><span><Icon name="check" size={14} /> Explainable results</span><span><Icon name="check" size={14} /> Source-backed answers</span><span><Icon name="check" size={14} /> Fictional demo data</span></div>
          </div>
          <LandingDashboardPreview />
        </section>

        <section className="landing-feature-strip" aria-label="Product principles">{landingFeatures.map((feature) => <article key={feature.title}><span><Icon name={feature.icon} size={21} /></span><div><h3>{feature.title}</h3><p>{feature.text}</p></div></article>)}</section>

        <section className="landing-section intelligence-section" id="about">
          <div className="landing-section-heading centered"><p className="landing-eyebrow">Designed for confidence</p><h2>Financial intelligence, without sacrificing trust.</h2><p>Understand your finances with an experience that keeps evidence, context, and control close to every answer.</p></div>
          <div className="intelligence-cards">
            <article><div className="large-card-icon"><Icon name="search" size={25} /></div><p className="card-number">01</p><h3>Transparent Answers</h3><p>See the category, date range, calculation, and source transactions used to produce each financial result.</p><div className="answer-proof"><span>Result traceability</span><b><Icon name="check" size={14} /> Verified sources</b></div></article>
            <article><div className="large-card-icon"><Icon name="spark" size={25} /></div><p className="card-number">02</p><h3>Explainable AI</h3><p>Financial answers should be understandable—not unexplained numbers generated behind a black box.</p><div className="answer-proof"><span>Calculation context</span><b><Icon name="check" size={14} /> Clear logic</b></div></article>
          </div>
        </section>

        <section className="landing-section process-section" id="how-it-works">
          <div className="landing-section-heading"><p className="landing-eyebrow">How it works</p><h2>From question to verified answer.</h2><p>A simple workflow that keeps you informed at every step.</p></div>
          <div className="process-grid">{[
            ["01", "Ask", "Ask a question about your financial data.", "search"],
            ["02", "Understand", "Ledger analyzes the relevant financial information.", "spark"],
            ["03", "Verify", "Review the data and supporting information behind the answer.", "shield"],
            ["04", "Decide", "Use the insight to better understand your finances.", "check"],
          ].map(([number, title, text, icon], index) => <article key={title}><span className="process-number">{number}</span><div className="process-icon"><Icon name={icon as IconName} size={20} /></div><h3>{title}</h3><p>{text}</p>{index < 3 && <Icon name="arrow" size={18} />}</article>)}</div>
        </section>

        <section className="governance-section" id="security">
          <div className="landing-section governance-inner">
            <div className="landing-section-heading light"><p className="landing-eyebrow">Security & governance</p><h2>Enterprise-grade governance meets effortless discovery.</h2><p>Financial information deserves careful handling. Ledger is designed around controlled access, clear logic, and accountable results.</p></div>
            <div className="governance-grid">{governance.map(([title, text, icon]) => <article key={title}><span><Icon name={icon as IconName} size={20} /></span><h3>{title}</h3><p>{text}</p></article>)}</div>
          </div>
        </section>

        <section className="landing-section trust-system">
          <div className="landing-section-heading centered"><p className="landing-eyebrow">A transparent system</p><h2>Built around trust, not just intelligence.</h2><p>Every stage is designed to preserve context from the original data through to the final answer.</p></div>
          <div className="system-layout">
            <div className="system-flow">{[["Financial Data", "wallet"], ["Secure Processing", "shield"], ["Financial Analysis", "chart"], ["Verified Answer", "check"]].map(([label, icon], index) => <div key={label}><span><Icon name={icon as IconName} size={20} /></span><strong>{label}</strong>{index < 3 && <Icon name="chevron" size={18} />}</div>)}</div>
            <div className="query-demo">
              <div className="query-demo-top"><Brand /><span>Financial question</span></div>
              <div className="demo-question"><span>AK</span><p>How much did I spend on transportation this month?</p></div>
              <div className="demo-answer"><p><Icon name="check" size={15} /> Verified financial answer</p><strong>₹2,450</strong><small>Transportation · September 2026 · 12 transactions</small><div><span>Calculation</span><b>SUM(amount)</b><span>Sources</span><b>12 records</b></div></div>
            </div>
          </div>
        </section>

        <section className="landing-section audience-section" id="features">
          <div className="landing-section-heading"><p className="landing-eyebrow">Built for modern teams</p><h2>Engineered for every tier of the modern organization.</h2><p>Clear financial understanding for everyone who needs to make informed decisions.</p></div>
          <div className="audience-grid">{[
            ["Finance Teams", "Move from totals to source transactions and explain financial results with confidence.", "chart"],
            ["Department Managers", "Understand team spending and the context behind category-level changes.", "user"],
            ["Employees", "Ask straightforward questions and receive clear, relevant financial answers.", "search"],
            ["Organizations", "Create a shared, governed layer for trustworthy financial understanding.", "shield"],
          ].map(([title, text, icon]) => <article key={title}><span><Icon name={icon as IconName} size={21} /></span><h3>{title}</h3><p>{text}</p><b>Explore use case <Icon name="arrow" size={14} /></b></article>)}</div>
        </section>

        <section className="landing-section final-cta">
          <div><p className="landing-eyebrow">Start with a question</p><h2>Your financial data already has the answers.</h2><p>Ask questions, understand your spending, and turn your financial data into actionable insights.</p></div>
          <div><Button className="primary landing-primary" onClick={() => navigate("/signup")}>Get Started <Icon name="arrow" size={18} /></Button><Button onClick={() => navigate("/login")}>Log In</Button></div>
        </section>
      </main>
      <footer className="landing-footer">
        <div className="footer-main"><div className="footer-brand"><Brand light /><p>Transparent financial analytics for clearer, more confident decisions.</p></div><div><strong>Product</strong><a href="#features">Features</a><a href="#how-it-works">How It Works</a><button onClick={() => navigate("/login")}>Log In</button></div><div><strong>Company</strong><a href="#about">About</a><span>Contact</span><span>Careers</span></div><div><strong>Trust</strong><a href="#security">Security</a><span>Privacy</span><span>Governance</span></div><div><strong>Contact</strong><span>hello@ledger.example</span><span>Financial intelligence,<br />explained.</span></div></div>
        <div className="footer-bottom"><span>© 2026 LEDGER. UI prototype.</span><span>Fictional financial data for demonstration only.</span></div>
      </footer>
    </div>
  );
}

function Dashboard({ onLogout, theme, onTheme }: { onLogout: () => void; theme: "light" | "dark"; onTheme: () => void }) {
  const [query, setQuery] = useState("");
  const [state, setState] = useState<ResultState>("idle");
  const [period, setPeriod] = useState<PeriodKey>("This Month");
  const [account, setAccount] = useState<AccountKey>("All Accounts");
  const [selectedCategory, setSelectedCategory] = useState("Housing");
  const [drillFilter, setDrillFilter] = useState<DrillFilter>("all");
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const transactionRef = useRef<HTMLDivElement>(null);

  const analytics = useMemo<Analytics>(() => {
    const source = periodData[period];
    const factor = accountFactors[account];
    const income = Math.round(source.income * factor.income);
    const expenses = Math.round(source.expenses * factor.expenses);
    const previousIncome = Math.round(source.previousIncome * factor.income);
    const previousExpenses = Math.round(source.previousExpenses * factor.expenses);
    const net = income - expenses;
    const previousNet = previousIncome - previousExpenses;
    return {
      periodLabel: source.label,
      income,
      expenses,
      net,
      balance: Math.round(source.balance * factor.balance),
      savingsRate: income ? (net / income) * 100 : 0,
      previousIncome,
      previousExpenses,
      previousNet,
      previousSavingsRate: previousIncome ? (previousNet / previousIncome) * 100 : 0,
    };
  }, [period, account]);

  const categories = useMemo<CategoryDatum[]>(() => {
    const multiplier = (periodData[period].expenses / periodData["This Month"].expenses) * accountFactors[account].expenses;
    const raw = categoryBase.map((category) => ({ ...category, amount: Math.round(category.amount * multiplier), count: Math.max(1, Math.round(category.count * Math.min(1, multiplier))) }));
    const difference = analytics.expenses - raw.reduce((sum, category) => sum + category.amount, 0);
    raw[0].amount += difference;
    return raw;
  }, [period, account, analytics.expenses]);

  const filteredTransactions = useMemo(() => {
    let rows = account === "All Accounts" ? workspaceTransactions : workspaceTransactions.filter((transaction) => transaction.account === account);
    const rowLimit: Record<PeriodKey, number> = { Today: 2, "This Week": 5, "This Month": 8, "Last Month": 8, "Last 3 Months": 8, "This Year": 8, "Custom Range": 7 };
    const expenseScale = analytics.expenses / periodData["This Month"].expenses;
    const incomeScale = analytics.income / periodData["This Month"].income;
    rows = rows.slice(0, rowLimit[period]).map((transaction, index) => ({
      ...transaction,
      date: period === "Today" ? "Sep 28, 2026" : period === "Last Month" ? transaction.date.replace("Sep", "Aug") : transaction.date,
      amount: Math.round(transaction.amount * (transaction.type === "income" ? incomeScale : expenseScale)),
      id: `${transaction.id}-${period.replace(/ /g, "").slice(0, 3)}-${index}`,
    }));
    if (drillFilter === "income") rows = rows.filter((transaction) => transaction.type === "income");
    else if (drillFilter === "expenses") rows = rows.filter((transaction) => transaction.type === "expense");
    else if (drillFilter !== "all" && drillFilter !== "savings") rows = rows.filter((transaction) => transaction.category === drillFilter);
    return rows;
  }, [account, analytics.expenses, analytics.income, drillFilter, period]);

  useEffect(() => {
    if (state !== "loading") return;
    const timer = window.setTimeout(() => setState("success"), 1150);
    return () => window.clearTimeout(timer);
  }, [state]);

  function submit() {
    setState("loading");
  }

  function reset() {
    setState("idle");
    setQuery("");
  }

  function runExample(text: string) {
    setQuery(text);
    setState("loading");
  }

  function drillDown(filter: DrillFilter) {
    setDrillFilter(filter);
    window.setTimeout(() => transactionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 30);
  }

  function changePeriod(nextPeriod: PeriodKey) {
    setPeriod(nextPeriod);
    setDrillFilter("all");
  }

  function changeAccount(nextAccount: AccountKey) {
    setAccount(nextAccount);
    setDrillFilter("all");
  }

  return (
    <div className="app-shell">
      <Header onLogout={onLogout} theme={theme} onTheme={onTheme} />
      <main className="dashboard">
        <section className="welcome">
          <div><p className="section-kicker">Monday, September 28</p><h1>Good morning, Alex.</h1><p>Explore your financial activity and trace every metric to its source.</p></div>
          <span className="workspace-status"><span className="status-dot" /> Analytics up to date</span>
        </section>
        <FilterBar period={period} account={account} onPeriod={changePeriod} onAccount={changeAccount} />
        <div className="analytics-content" key={`${period}-${account}`}>
          <section className="summary-grid">
            <SummaryCard icon="wallet" label="Total balance" value={formatMoney(analytics.balance, true)} change={percentChange(analytics.balance, analytics.balance - analytics.net)} comparison="vs previous period" accent onClick={() => drillDown("savings")} spark={[18, 17, 14, 15, 11, 9]} />
            <SummaryCard icon="receipt" label="Income" value={formatMoney(analytics.income, true)} change={percentChange(analytics.income, analytics.previousIncome)} comparison="vs previous period" onClick={() => drillDown("income")} spark={[21, 18, 19, 14, 13, 8]} />
            <SummaryCard icon="chart" label="Total expenses" value={formatMoney(analytics.expenses, true)} change={percentChange(analytics.expenses, analytics.previousExpenses)} comparison="vs previous period" onClick={() => drillDown("expenses")} spark={[10, 13, 11, 15, 17, 16]} />
            <SummaryCard icon="budget" label="Savings rate" value={`${analytics.savingsRate.toFixed(1)}%`} change={analytics.savingsRate - analytics.previousSavingsRate} comparison="vs previous period" onClick={() => drillDown("savings")} spark={[20, 18, 17, 14, 12, 8]} />
          </section>
        </div>
        <QueryBox query={query} setQuery={setQuery} submit={submit} loading={state === "loading"} />

        {state === "idle" && (
          <>
            <div className="analytics-workspace analytics-content" key={`workspace-${period}-${account}`}>
              <div className="analytics-primary">
                <CashFlowChart analytics={analytics} />
                <IncomeExpensePanel analytics={analytics} />
              </div>
              <SpendingCategories categories={categories} selected={selectedCategory} onSelect={setSelectedCategory} onView={() => drillDown(selectedCategory)} />
              <FinancialInsights analytics={analytics} categories={categories} />
              <div ref={transactionRef}><RecentTransactions rows={filteredTransactions} filter={drillFilter} onClear={() => setDrillFilter("all")} onOpen={setSelectedTransaction} /></div>
              <section className="below-grid">
                <div className="recent panel">
                  <div className="panel-heading"><div><p className="section-kicker">Your activity</p><h3>Recent questions</h3></div><Icon name="clock" size={19} /></div>
                  <div className="recent-list">
                    {examples.slice(0, 3).map((item, index) => <Button key={item} onClick={() => runExample(item)}><span className="recent-icon"><Icon name={index === 0 ? "food" : index === 1 ? "wallet" : "chart"} size={18} /></span><span><strong>{item}</strong><small>{index === 0 ? "Today, 9:42 AM" : index === 1 ? "Yesterday" : "Sep 24, 2026"}</small></span><Icon name="arrow" size={17} /></Button>)}
                  </div>
                </div>
                <div className="demo-panel panel">
                  <div className="panel-heading"><div><p className="section-kicker">Prototype preview</p><h3>Explore result states</h3></div><Icon name="spark" size={19} /></div>
                  <p>Preview how LEDGER responds when a query needs more context or cannot return a result.</p>
                  <div className="demo-buttons">
                    <Button onClick={() => { setQuery("How much did I spend recently?"); setState("clarification"); }}><span className="demo-dot amber" /> Clarification</Button>
                    <Button onClick={() => { setQuery("Predict my investment returns"); setState("refusal"); }}><span className="demo-dot red" /> Unsupported request</Button>
                    <Button onClick={() => { setQuery("Food spending in August 2026"); setState("empty"); }}><span className="demo-dot gray" /> No matching data</Button>
                    <Button onClick={() => { setQuery("Show this month's expenses"); setState("error"); }}><span className="demo-dot red" /> System error</Button>
                  </div>
                </div>
              </section>
            </div>
          </>
        )}
        {state === "loading" && <LoadingState />}
        {state === "success" && <div className="results"><ResultCard /><div className="result-grid"><ContextPanel /><CalculationPanel /></div><ChartPanel /><SourceRowsTable /></div>}
        {!["idle", "loading", "success"].includes(state) && <StatusState type={state as "clarification" | "refusal" | "empty" | "error"} onAction={(next) => next ? setState(next) : reset()} />}
      </main>
      <footer className="app-footer"><span>LEDGER UI prototype · Fictional financial data for demonstration only</span><span><Icon name="shield" size={14} /> Transparent by design</span></footer>
      {selectedTransaction && <TransactionDrawer transaction={selectedTransaction} onClose={() => setSelectedTransaction(null)} />}
    </div>
  );
}

function AuthRoute({ mode }: { mode: "login" | "signup" }) {
  const navigate = useNavigate();
  return <Login key={mode} initialView={mode} onLogin={() => navigate("/dashboard")} onView={(next) => navigate(`/${next}`)} />;
}

function DashboardRoute() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  return <Dashboard onLogout={() => navigate("/login")} theme={theme} onTheme={toggleTheme} />;
}

function AdminRoute() {
  return <AdminPortal />;
}

const router = createBrowserRouter([
  { path: "/", Component: LandingPage },
  { path: "/login", element: <AuthRoute mode="login" /> },
  { path: "/signup", element: <AuthRoute mode="signup" /> },
  { path: "/dashboard", Component: DashboardRoute },

  { path: "/admin", Component: AdminRoute },

  { path: "*", Component: LandingPage },
]);

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = window.localStorage.getItem("ledger-theme");
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    window.localStorage.setItem("ledger-theme", theme);
  }, [theme]);

  return <ThemeContext.Provider value={{ theme, toggleTheme: () => setTheme((current) => current === "light" ? "dark" : "light") }}><RouterProvider router={router} /></ThemeContext.Provider>;
}
