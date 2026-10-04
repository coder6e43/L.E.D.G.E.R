import { Icon } from "../common/Icon";
import { Brand } from "../common/Brand";

export function LandingDashboardPreview() {
  const miniBars = [
    48,
    64,
    52,
    76,
    68,
    88,
    80,
  ];

  return (
    <div className="landing-preview-wrap">
      <div className="preview-orbit orbit-one" />
      <div className="preview-orbit orbit-two" />

      <div className="landing-dashboard-preview">
        <div className="preview-topbar">
          <Brand />

          <span>
            <i /> Live overview
          </span>
        </div>

        <div className="preview-content">
          <div className="preview-heading">
            <span>Financial overview</span>
            <b>September 2026</b>
          </div>

          <div className="preview-kpis">
            <div>
              <span>Total balance</span>
              <strong>₹12.49L</strong>
              <small className="change-positive">
                ↑ 4.8%
              </small>
            </div>

            <div>
              <span>Income</span>
              <strong>₹1.42L</strong>
              <small className="change-positive">
                ↑ 0.4%
              </small>
            </div>

            <div>
              <span>Expenses</span>
              <strong>₹84,250</strong>
              <small className="change-positive">
                ↓ 4.7%
              </small>
            </div>
          </div>

          <div className="preview-grid">
            <div className="preview-chart">
              <div>
                <span>Cash flow</span>
                <small>Last 7 months</small>
              </div>

              <div className="mini-chart">
                {miniBars.map((height, index) => (
                  <span key={index}>
                    <i
                      style={{
                        height: `${height}%`,
                      }}
                    />

                    <b
                      style={{
                        height: `${Math.max(
                          24,
                          height - 28
                        )}%`,
                      }}
                    />
                  </span>
                ))}
              </div>

              <div className="mini-legend">
                <span>Income</span>
                <span>Expenses</span>
              </div>
            </div>

            <div className="preview-breakdown">
              <span>Top spending</span>

              {[
                ["Housing", "₹28,000", 100],
                ["Food", "₹12,450", 45],
                ["Shopping", "₹9,200", 33],
              ].map(
                ([label, value, width]) => (
                  <div key={label as string}>
                    <p>
                      <span>{label}</span>
                      <b>{value}</b>
                    </p>

                    <i>
                      <span
                        style={{
                          width: `${width}%`,
                        }}
                      />
                    </i>
                  </div>
                )
              )}
            </div>
          </div>

          <div className="preview-transactions">
            <div>
              <span>Recent transactions</span>
              <small>View all</small>
            </div>

            {[
              [
                "Fresh Market",
                "Food",
                "−₹2,450",
              ],
              [
                "Acme Technologies",
                "Income",
                "+₹1,42,000",
              ],
            ].map((row) => (
              <div key={row[0]}>
                <span className="preview-merchant">
                  {row[0].slice(0, 1)}
                </span>

                <p>
                  <b>{row[0]}</b>
                  <small>{row[1]}</small>
                </p>

                <strong
                  className={
                    row[2].startsWith("+")
                      ? "change-positive"
                      : ""
                  }
                >
                  {row[2]}
                </strong>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="preview-trust-chip">
        <Icon name="shield" size={17} />

        <span>
          <strong>Evidence backed</strong>
          <small>Every result is traceable</small>
        </span>
      </div>
    </div>
  );
}