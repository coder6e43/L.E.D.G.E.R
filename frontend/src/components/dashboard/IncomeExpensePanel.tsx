import { useState } from "react";
import { Button } from "../common/Button";
import { formatMoney, percentChange } from "../../utils/formatters";
import type { Analytics } from "../../types";

export function IncomeExpensePanel({ analytics }: { analytics: Analytics }) {
  const [metric, setMetric] = useState<"Income" | "Expenses" | "Net">("Income");
  const metrics = {
    Income: { value: analytics.income, previous: analytics.previousIncome, className: "income" },
    Expenses: { value: analytics.expenses, previous: analytics.previousExpenses, className: "expenses" },
    Net: { value: analytics.net, previous: analytics.previousNet, className: "net" },
  };
  const selected = metrics[metric];
  const change = percentChange(selected.value, selected.previous);
  const max = Math.max(selected.value, selected.previous);
  return (
    <section className="panel comparison-panel">
      <div className="panel-heading"><div><p className="section-kicker">Period comparison</p><h3>Income vs expenses</h3><small>Compared with previous period</small></div></div>
      <div className="metric-tabs">{(Object.keys(metrics) as Array<keyof typeof metrics>).map((item) => <Button key={item} className={metric === item ? "selected" : ""} onClick={() => setMetric(item)}>{item}</Button>)}</div>
      <div className="comparison-value"><span>{metric}</span><strong>{formatMoney(selected.value)}</strong><small className={change >= 0 ? "change-positive" : "change-negative"}>{change >= 0 ? "↑" : "↓"} {Math.abs(change).toFixed(1)}% vs previous period</small></div>
      <div className="comparison-bars">
        <div><span>Current</span><div><i className={selected.className} style={{ width: `${(selected.value / max) * 100}%` }}><b>{formatMoney(selected.value)}</b></i></div></div>
        <div><span>Previous</span><div><i className="previous" style={{ width: `${(selected.previous / max) * 100}%` }}><b>{formatMoney(selected.previous)}</b></i></div></div>
      </div>
      <div className="equation"><span>{formatMoney(analytics.income)} income</span><b>−</b><span>{formatMoney(analytics.expenses)} expenses</span><b>=</b><strong>{formatMoney(analytics.net)} net</strong></div>
    </section>
  );
}
