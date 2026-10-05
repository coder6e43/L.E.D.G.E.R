import { useState } from "react";
import { Button } from "../common/Button";
import { formatMoney } from "../../utils/formatters";
import type { Analytics } from "../../types";

export function CashFlowChart({ analytics }: { analytics: Analytics }) {
  const [range, setRange] = useState("6M");
  const [hovered, setHovered] = useState<number | null>(null);
  const rangeOptions = ["7D", "30D", "3M", "6M", "1Y"];
  const rangeFactors: Record<string, number> = { "7D": .07, "30D": .24, "3M": .55, "6M": 1, "1Y": 1.8 };
  const f = rangeFactors[range];
  const labels = range === "7D" ? ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] : range === "30D" ? ["Sep 1", "Sep 6", "Sep 11", "Sep 16", "Sep 21", "Sep 26", "Sep 30"] : range === "1Y" ? ["Oct", "Dec", "Feb", "Apr", "Jun", "Aug", "Sep"] : ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Current"];
  const incomeWeights = [.72, .84, .79, .91, .86, .96, 1];
  const expenseWeights = [.81, .76, .88, .82, 1.05, .95, 1];
  const points = labels.map((label, index) => {
    const income = analytics.income * f * incomeWeights[index];
    const expenses = analytics.expenses * f * expenseWeights[index];
    return { label, income, expenses, net: income - expenses };
  });
  const maxValue = Math.max(...points.flatMap((point) => [point.income, point.expenses])) * 1.12;
  const minValue = Math.min(0, ...points.map((point) => point.net)) * 1.12;
  const x = (index: number) => 48 + index * (602 / (points.length - 1));
  const y = (value: number) => 190 - ((value - minValue) / (maxValue - minValue)) * 150;
  const incomeLine = points.map((point, index) => `${x(index)},${y(point.income)}`).join(" ");
  const expenseLine = points.map((point, index) => `${x(index)},${y(point.expenses)}`).join(" ");
  const netLine = points.map((point, index) => `${x(index)},${y(point.net)}`).join(" ");

  return (
    <section className="panel cashflow-panel">
      <div className="panel-heading">
        <div><p className="section-kicker">Cash flow</p><h3>Income, expenses & net</h3><small>Historical performance · {range}</small></div>
        <div className="segmented" aria-label="Cash flow range">{rangeOptions.map((option) => <Button key={option} className={range === option ? "selected" : ""} onClick={() => { setRange(option); setHovered(null); }}>{option}</Button>)}</div>
      </div>
      <div className="chart-legend"><span className="legend-income">Income</span><span className="legend-expense">Expenses</span><span className="legend-net">Net cash flow</span><small>Shaded area marks the current period</small></div>
      <div className="cashflow-chart">
        <svg viewBox="0 0 700 230" role="img" aria-label={`Cash flow chart for ${range}`}>
          <rect className="current-period-band" x="615" y="18" width="70" height="182" rx="5" />
          {[40, 90, 140, 190].map((line) => <line key={line} className="grid-line" x1="48" y1={line} x2="650" y2={line} />)}
          <polyline className="cash-line income-line" points={incomeLine} />
          <polyline className="cash-line expense-line" points={expenseLine} />
          <polyline className="cash-line net-line" points={netLine} />
          {points.map((point, index) => (
            <g key={point.label} onMouseEnter={() => setHovered(index)} onMouseLeave={() => setHovered(null)} className="chart-hit">
              <rect x={x(index) - 22} y="18" width="44" height="185" fill="transparent" />
              <circle className="income-point" cx={x(index)} cy={y(point.income)} r={hovered === index ? 5 : 3} />
              <circle className="expense-point" cx={x(index)} cy={y(point.expenses)} r={hovered === index ? 5 : 3} />
              <text className="axis-label" x={x(index)} y="219" textAnchor="middle">{point.label}</text>
            </g>
          ))}
        </svg>
        {hovered !== null && <div className="chart-tooltip" style={{ left: `${Math.min(82, 8 + hovered * 13)}%` }}><strong>{points[hovered].label}</strong><span><i className="income-dot" />Income <b>{formatMoney(points[hovered].income)}</b></span><span><i className="expense-dot" />Expenses <b>{formatMoney(points[hovered].expenses)}</b></span><span><i className="net-dot" />Net cash flow <b>{formatMoney(points[hovered].net)}</b></span></div>}
      </div>
    </section>
  );
}
