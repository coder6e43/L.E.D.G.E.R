import { Icon } from "../common/Icon";

export function CalculationPanel() {
  return (
    <section className="panel calculation-panel">
      <div className="panel-heading"><div><p className="section-kicker">Method</p><h3>How this was calculated</h3></div><span className="verified"><Icon name="check" size={14} /> Verified</span></div>
      <div className="formula"><span>Calculation supplied</span><code>SUM ( amount )</code></div>
      <div className="calc-flow">
        <div><span>01</span><p>Matched transactions<strong>37 records</strong></p></div>
        <Icon name="chevron" size={17} />
        <div><span>02</span><p>Aggregation<strong>Sum of amount</strong></p></div>
        <Icon name="chevron" size={17} />
        <div className="calc-total"><span>03</span><p>Result<strong>₹12,450</strong></p></div>
      </div>
      <details><summary>View calculation details <Icon name="chevron" size={16} /></summary><p>Amounts from 37 matching expense transactions were aggregated using the supplied formula. No calculation is performed in this prototype.</p></details>
    </section>
  );
}
