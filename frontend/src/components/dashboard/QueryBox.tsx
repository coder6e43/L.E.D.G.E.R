import { useState } from "react";
import type { FormEvent } from "react";
import { Icon } from "../common/Icon";
import { Button } from "../common/Button";

export function QueryBox({ query, setQuery, submit, loading, examples }: { query: string; setQuery: (value: string) => void; submit: () => void; loading: boolean; examples: string[] }) {
  const [validation, setValidation] = useState(false);
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) {
      setValidation(true);
      return;
    }
    setValidation(false);
    submit();
  }
  return (
    <section className="query-section">
      <div className="section-title-row">
        <div><p className="section-kicker">Financial search</p><h2>What would you like to know?</h2></div>
        <span className="data-note"><span className="status-dot" /> Connected to your workspace</span>
      </div>
      <form className={`query-form ${validation ? "invalid" : ""}`} onSubmit={handleSubmit}>
        <Icon name="search" size={23} />
        <input
          aria-label="Financial question"
          value={query}
          onChange={(event) => { setQuery(event.target.value); setValidation(false); }}
          placeholder="Ask about spending, categories, dates, or budgets…"
        />
        <Button className="primary" type="submit" disabled={loading}>{loading ? "Analyzing…" : <>Ask question <Icon name="arrow" size={18} /></>}</Button>
      </form>
      {validation && <p className="validation"><Icon name="warning" size={15} /> Enter a financial question to continue.</p>}
      <div className="suggestions"><span>Try asking</span>{examples.map((example) => <Button key={example} className="suggestion" onClick={() => setQuery(example)}>{example}</Button>)}</div>
    </section>
  );
}
