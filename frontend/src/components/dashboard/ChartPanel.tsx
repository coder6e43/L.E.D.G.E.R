import { Icon } from "../common/Icon";

const bars = [
  {
    label: "Food & Dining",
    value: "₹12,450",
    width: "100%",
    primary: true,
  },
  {
    label: "Transport",
    value: "₹6,200",
    width: "50%",
  },
  {
    label: "Shopping",
    value: "₹4,500",
    width: "36%",
  },
  {
    label: "Entertainment",
    value: "₹2,300",
    width: "18%",
  },
];

export function ChartPanel() {
  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Visualization</p>
          <h3>Spending by category</h3>
          <small>September 2026 · Expenses</small>
        </div>

        <span className="chart-type">
          <Icon name="chart" size={16} /> Comparison
        </span>
      </div>

      <div
        className="chart"
        role="img"
        aria-label="Horizontal bar chart comparing spending across four categories"
      >
        <div className="chart-axis" aria-hidden="true">
          <span>Category</span>
          <span>₹0</span>
          <span>₹6,225</span>
          <span>₹12,450</span>
          <strong>Amount</strong>
        </div>

        <div className="chart-rows">
          {bars.map((bar) => (
            <div className="bar-row" key={bar.label}>
              <span>{bar.label}</span>

              <div className="bar-track">
                <i
                  className={bar.primary ? "primary-bar" : ""}
                  style={{ width: bar.width }}
                />
              </div>

              <strong>{bar.value}</strong>
            </div>
          ))}
        </div>
      </div>

      <p className="chart-caption">
        <Icon name="info" size={15} /> Food & Dining represents the largest
        category in the displayed data.
      </p>
    </section>
  );
}