import { Button } from "../common/Button";
import { Icon } from "../common/Icon";
import { formatMoney } from "../../utils/formatters";
import type { CategoryDatum } from "../../types";

export function SpendingCategories({ categories, selected, onSelect, onView }: { categories: CategoryDatum[]; selected: string; onSelect: (name: string) => void; onView: () => void }) {
  const total = categories.reduce((sum, category) => sum + category.amount, 0);
  const active = categories.find((category) => category.name === selected) || categories[0];
  const max = Math.max(...categories.map((category) => category.amount));
  return (
    <section className="panel categories-panel">
      <div className="panel-heading"><div><p className="section-kicker">Spending breakdown</p><h3>Spending by category</h3><small>Click a category to inspect its contribution</small></div><span className="chart-type">{formatMoney(total)} total</span></div>
      <div className="category-layout">
        <div className="category-bars">
          {categories.map((category, index) => <button key={category.name} className={`category-row ${selected === category.name ? "selected" : ""}`} onClick={() => onSelect(category.name)}><span><i className={`category-swatch category-${index}`} />{category.name}</span><div><i className={`category-fill category-${index}`} style={{ width: `${(category.amount / max) * 100}%` }} /></div><strong>{formatMoney(category.amount)}</strong></button>)}
        </div>
        <aside className="category-detail">
          <p>Selected category</p>
          <h4>{active.name}</h4>
          <strong>{formatMoney(active.amount)}</strong>
          <div><span><small>Share of spending</small><b>{((active.amount / total) * 100).toFixed(1)}%</b></span><span><small>Transactions</small><b>{active.count}</b></span></div>
          <Button className="secondary" onClick={onView}>View transactions <Icon name="arrow" size={15} /></Button>
        </aside>
      </div>
    </section>
  );
}
