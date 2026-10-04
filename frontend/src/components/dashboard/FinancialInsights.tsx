import { formatMoney, percentChange } from "../../utils/formatters";
import type { Analytics, CategoryDatum } from "../../types";

export function FinancialInsights({ analytics, categories }: { analytics: Analytics; categories: CategoryDatum[] }) {
  const expenseChange = percentChange(analytics.expenses, analytics.previousExpenses);
  const savingsChange = analytics.savingsRate - analytics.previousSavingsRate;
  const food = categories.find((category) => category.name === "Food");
  const subscriptions = categories.find((category) => category.name === "Subscriptions");
  const total = categories.reduce((sum, category) => sum + category.amount, 0);
  const insights = [
    { tone: expenseChange <= 0 ? "positive" : "warning", metric: `${Math.abs(expenseChange).toFixed(1)}%`, title: `Expenses ${expenseChange <= 0 ? "decreased" : "increased"}`, text: `Compared with the previous period (${formatMoney(analytics.previousExpenses)}).` },
    { tone: "warning", metric: `${((food?.amount ?? 0) / total * 100).toFixed(1)}%`, title: "Food spending share", text: `${formatMoney(food?.amount ?? 0)} of your displayed expenses are in the Food category.`,},
    { tone: "positive", metric: `+${savingsChange.toFixed(1)} pp`, title: "Savings rate improved", text: `Increased from ${analytics.previousSavingsRate.toFixed(1)}% to ${analytics.savingsRate.toFixed(1)}%.` },
    { tone: "neutral", metric: `${(((subscriptions?.amount ?? 0) / total) * 100).toFixed(1)}%`, title: "Subscription share", text: subscriptions ? `${formatMoney(subscriptions.amount)} across ${subscriptions.count} transactions.` : "No subscription transactions in this period." },
  ];
  return (
    <section className="panel insights-panel">
      <div className="panel-heading"><div><p className="section-kicker">Financial insights</p><h3>What changed this period</h3><small>Derived from the analytics currently displayed</small></div></div>
      <div className="insight-grid">{insights.map((insight) => <article key={insight.title} className={`insight ${insight.tone}`}><span>{insight.metric}</span><div><strong>{insight.title}</strong><p>{insight.text}</p></div></article>)}</div>
    </section>
  );
}