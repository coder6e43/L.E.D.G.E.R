import { Icon } from "../common/Icon";

export function ResultCard() {
  return (
    <section className="result-card">
      <div className="result-top">
        <div>
          <p className="result-label"><span><Icon name="check" size={14} /></span> Financial result</p>
          <p className="answered-query">How much did I spend on food this month?</p>
        </div>
        <span className="result-status"><Icon name="shield" size={15} /> Supported by source data</span>
      </div>
      <div className="result-main">
        <div className="answer">
          <span>Total spending</span>
          <strong>₹12,450</strong>
          <small>for September 2026</small>
        </div>
        <div className="result-divider" />
        <div className="answer-context">
          <div><span className="context-icon"><Icon name="food" size={19} /></span><span><small>Category</small><strong>Food & Dining</strong></span></div>
          <div><span className="context-icon"><Icon name="calendar" size={19} /></span><span><small>Date range</small><strong>Sep 1 – Sep 30, 2026</strong></span></div>
          <div><span className="context-icon"><Icon name="receipt" size={19} /></span><span><small>Evidence</small><strong>37 transactions</strong></span></div>
        </div>
      </div>
    </section>
  );
}
