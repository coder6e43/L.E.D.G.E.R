import { Icon } from "../common/Icon";

export function ContextPanel() {
  return (
    <section className="panel context-panel">
      <div className="panel-heading"><div><p className="section-kicker">Query context</p><h3>Scope of this result</h3></div><Icon name="info" size={19} /></div>
      <div className="metadata-grid">
        <div><span>Category</span><strong>Food & Dining</strong></div>
        <div><span>Date range</span><strong>Sep 1 – Sep 30, 2026</strong></div>
        <div><span>Account</span><strong>Primary account</strong></div>
        <div><span>Transaction type</span><strong>Expenses</strong></div>
      </div>
      <div className="filters"><span>Filters applied</span><b>Food & Dining <i>×</i></b><b>Sep 1–30, 2026 <i>×</i></b><b>Expenses <i>×</i></b></div>
    </section>
  );
}
