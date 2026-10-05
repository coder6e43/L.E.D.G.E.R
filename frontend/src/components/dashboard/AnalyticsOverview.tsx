import { useMemo, useState } from "react";
import type { AnalyticsOverview as Overview } from "../../services/api";
import { SpendingCategories } from "./SpendingCategories";
import type { CategoryDatum } from "../../types";
import { formatMoney } from "../../utils/formatters";

export function AnalyticsOverview({ data, onAsk }: { data: Overview; onAsk: (prompt: string) => void }) {
  const currencies = [...new Set(data.monthly_spending.map((item) => item.currency))];
  const [currency, setCurrency] = useState(currencies[0] || "INR");
  const activeCurrency = currencies.includes(currency) ? currency : currencies[0] || "INR";
  const months = useMemo(() => [...new Set(data.monthly_spending.map((item) => item.month))], [data.monthly_spending]);
  const points = months.map((month) => data.monthly_spending.find((item) => item.month === month && item.currency === activeCurrency)?.amount || 0);
  const max = Math.max(1, ...points);
  const categories: CategoryDatum[] = data.category_spending.filter((item) => item.currency === activeCurrency).map((item) => ({ name: item.category, amount: item.amount, count: item.count, currency: item.currency }));
  const [selected, setSelected] = useState("");
  const scopeName = data.scope.scope_type === "user" ? "Your expenses" : data.scope.scope_type === "cost_centre" ? `Cost centre ${data.scope.scope_value}` : "Organization";
  return <section className="real-analytics" aria-label="Expense analytics">
    <div className="analytics-heading"><div><p className="section-kicker">Database analytics · {scopeName}</p><h2>Spending overview</h2><p>{data.period.start} through {data.period.end}</p></div>
      {currencies.length > 1 && <label className="compact-field">Currency<select value={activeCurrency} onChange={(event) => setCurrency(event.target.value)}>{currencies.map((value) => <option key={value}>{value}</option>)}</select></label>}
    </div>
    <div className="real-summary-grid">
      <article className="panel real-summary"><small>Expenses in period</small><strong>{data.expense_count.toLocaleString()}</strong><span>Authorized records</span></article>
      {data.spend_by_currency.map((item) => <article className="panel real-summary" key={item.currency}><small>Spend · {item.currency}</small><strong>{formatMoney(item.amount, item.currency)}</strong><span>{item.count} records · selected date range</span></article>)}
    </div>
    <div className="real-analytics-grid">
      <section className="panel monthly-panel"><div className="panel-heading"><div><p className="section-kicker">Monthly totals</p><h3>Spending trend</h3></div><span className="chart-type">{activeCurrency}</span></div>
        {points.some((value) => value > 0) ? <div className="monthly-chart" role="img" aria-label={`Monthly spending in ${activeCurrency}`}>
          {points.map((value, index) => <div className="monthly-column" key={months[index]} title={`${months[index]}: ${formatMoney(value, activeCurrency)}`}><span className="monthly-value">{value ? formatMoney(value, activeCurrency, true) : ""}</span><i style={{ height: `${value > 0 ? Math.max(3, value / max * 100) : 0}%` }} /><small>{months[index].slice(5)}</small></div>)}
        </div> : <p className="analytics-empty">No expenses are recorded for this currency in the displayed period.</p>}
      </section>
      <SpendingCategories categories={categories} selected={selected} onSelect={setSelected} onView={() => onAsk(`How much did I spend on ${selected || categories[0]?.name || "Food"} this year?`)} />
    </div>
    {!data.budget_comparison.available && <p className="analytics-note">Budget comparison unavailable: {data.budget_comparison.reason}</p>}
  </section>;
}
