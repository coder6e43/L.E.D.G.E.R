import { Icon } from "../common/Icon";
import type { IconName } from "../common/Icon";

export function SummaryCard({
  icon,
  label,
  value,
  change,
  comparison,
  accent,
  onClick,
  spark,
}: {
  icon: IconName;
  label: string;
  value: string;
  change: number;
  comparison: string;
  accent?: boolean;
  onClick: () => void;
  spark: number[];
}) {
  const positive = change >= 0;
  const points = spark.map((value, index) => `${index * 16},${28 - value}`).join(" ");
  return (
    <button className="summary-card" onClick={onClick}>
      <div className="summary-card-top"><div className={`summary-icon ${accent ? "accent" : ""}`}><Icon name={icon} /></div><span>View details <Icon name="arrow" size={14} /></span></div>
      <div className="summary-value"><p>{label}</p><strong>{value}</strong></div>
      <div className="summary-comparison">
        <span className={positive ? "change-positive" : "change-negative"}>{positive ? "↑" : "↓"} {Math.abs(change).toFixed(1)}{label === "Savings rate" ? " pp" : "%"}</span>
        <small>{comparison}</small>
        <svg viewBox="0 0 80 30" aria-hidden="true"><polyline points={points} /></svg>
      </div>
    </button>
  );
}
