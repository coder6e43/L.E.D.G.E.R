import { Button } from "../common/Button";
import { Icon } from "../common/Icon";
import { formatMoney } from "../../utils/formatters";
import type { CategoryDatum } from "../../types";

export function SpendingCategories({ categories, selected, onSelect, onView }: { categories: CategoryDatum[]; selected: string; onSelect: (name: string) => void; onView: () => void }) {
  const total = categories.reduce((sum, category) => sum + category.amount, 0);
  const currency = categories[0]?.currency || "INR";
  const active = categories.find((category) => category.name === selected) || categories[0];
  const max = Math.max(0, ...categories.map((category) => category.amount));
  return (
    <section className="panel categories-panel">
      <div className="panel-heading"><div><p className="section-kicker">Spending breakdown</p><h3>Spending by category</h3><small>Click a category to inspect its contribution</small></div><span className="chart-type">{formatMoney(total, currency)} total</span></div>
      <div className="category-layout">
        <div className="category-bars">
          {categories.map((category, index) => <button key={category.name} className={`category-row ${selected === category.name ? "selected" : ""}`} onClick={() => onSelect(category.name)}><span><i className={`category-swatch category-${index}`} />{category.name}</span><div><i className={`category-fill category-${index}`} style={{ width: `${max > 0 ? (category.amount / max) * 100 : 0}%` }} /></div><strong>{formatMoney(category.amount, category.currency || "INR")}</strong></button>)}
        </div>
        <aside className="category-detail">
          <p>Selected category</p>
          <h4>{active?.name || "No spending recorded"}</h4>
          <strong>{active ? formatMoney(active.amount, active.currency || "INR") : "—"}</strong>
          <div><span><small>Share of spending</small><b>{total > 0 && active ? `${((active.amount / total) * 100).toFixed(1)}%` : "—"}</b></span><span><small>Transactions</small><b>{active?.count ?? 0}</b></span></div>
          <Button className="secondary" onClick={onView}>View transactions <Icon name="arrow" size={15} /></Button>
        </aside>
      </div>
    </section>
  );
}
