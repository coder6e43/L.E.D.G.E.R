

export function LoadingState() {
  return (
    <section className="state-card loading-state" aria-live="polite">
      <div className="loader"><span /><span /><span /></div>
      <div><h3>Analyzing your financial question</h3><p>Reviewing the query context and preparing the supplied result…</p></div>
    </section>
  );
}
