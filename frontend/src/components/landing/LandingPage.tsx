import { Icon } from "../common/Icon";
import { LandingHeader } from "./LandingHeader";
import { LandingDashboardPreview } from "./LandingDashboardPreview";
import { useTheme } from "../../App";

export function LandingPage() {
  const { theme } = useTheme();

  const handleGetStarted = () => {
    window.location.href = "/login";
  };

  return (
    <div className={`landing-page ${theme === "dark" ? "dark" : ""}`}>
      <LandingHeader />

      <main>
        {/* =====================================================
            HERO
            ===================================================== */}
        <section id="home" className="landing-hero landing-hero-centered">
          <div className="landing-container hero-centered-container">

            {/* HERO TEXT */}
            <div className="hero-copy hero-copy-centered">
              <div className="landing-eyebrow">
                <span className="eyebrow-dot" />
                Evidence-backed financial intelligence
              </div>

              <h1>
                Ask your financial data.
                <span> Get answers you can trust.</span>
              </h1>

              <p className="hero-description">
                L.E.D.G.E.R. turns natural-language financial questions into
                secure, traceable answers backed by your actual data.
              </p>

              <div className="hero-actions">
                <button
                  className="landing-button primary"
                  onClick={handleGetStarted}
                >
                  Get Started
                  <Icon name="arrow" size={17} />
                </button>

                <a
                  className="landing-button secondary"
                  href="#how-it-works"
                >
                  See how it works
                  <Icon name="arrow" size={16} />
                </a>
              </div>

              <div className="hero-trust">
                <div className="trust-item">
                  <Icon name="shield" size={16} />
                  <span>Secure by design</span>
                </div>

                <div className="trust-divider" />

                <div className="trust-item">
                  <Icon name="check" size={16} />
                  <span>Evidence backed</span>
                </div>

                <div className="trust-divider" />

                <div className="trust-item">
                  <Icon name="shield" size={16} />
                  <span>Role-based access</span>
                </div>
              </div>
            </div>

            {/* DASHBOARD PREVIEW */}
            <div className="hero-visual hero-visual-centered">
              <LandingDashboardPreview />
            </div>

          </div>
        </section>

        {/* =====================================================
            ABOUT
            ===================================================== */}
        <section id="about" className="landing-section about-section">
          <div className="landing-container">
            <div className="section-heading centered">
              <span className="landing-eyebrow">
                About L.E.D.G.E.R.
              </span>

              <h2>
                Financial answers should come
                <span> with proof.</span>
              </h2>

              <p>
                L.E.D.G.E.R. is a secure financial query layer that connects
                natural-language questions with authorized business data,
                deterministic calculations and auditable evidence.
              </p>
            </div>

            <div className="about-grid">
              <article className="about-card">
                <div className="feature-icon">
                  <Icon name="search" size={20} />
                </div>

                <h3>Ask naturally</h3>

                <p>
                  Ask questions about expenses, spending and financial trends
                  without needing to know database queries.
                </p>
              </article>

              <article className="about-card">
                <div className="feature-icon">
                  <Icon name="shield" size={20} />
                </div>

                <h3>Stay within your scope</h3>

                <p>
                  Authentication and role-based access determine exactly which
                  records a user is allowed to access.
                </p>
              </article>

              <article className="about-card">
                <div className="feature-icon">
                  <Icon name="check" size={20} />
                </div>

                <h3>Trust the calculation</h3>

                <p>
                  Financial numbers are calculated from authorized records
                  rather than being invented by an AI model.
                </p>
              </article>
            </div>
          </div>
        </section>

        {/* =====================================================
            HOW IT WORKS
            ===================================================== */}
        <section
          id="how-it-works"
          className="landing-section process-section"
        >
          <div className="landing-container">
            <div className="section-heading">
              <span className="landing-eyebrow">
                How it works
              </span>

              <h2>
                From question to answer
                <span> without losing the trail.</span>
              </h2>

              <p>
                L.E.D.G.E.R. separates language understanding, authorization,
                calculation and evidence so every result remains explainable.
              </p>
            </div>

            <div className="process-grid">
              <article className="process-card">
                <span className="process-number">01</span>

                <div className="process-icon">
                  <Icon name="search" size={21} />
                </div>

                <h3>Ask</h3>

                <p>
                  Type a question in everyday language, such as
                  “How much did we spend on Food this month?”
                </p>
              </article>

              <article className="process-card">
                <span className="process-number">02</span>

                <div className="process-icon">
                  <Icon name="spark" size={21} />
                </div>

                <h3>Understand</h3>

                <p>
                  The query compiler converts your question into a structured
                  financial request.
                </p>
              </article>

              <article className="process-card">
                <span className="process-number">03</span>

                <div className="process-icon">
                  <Icon name="shield" size={21} />
                </div>

                <h3>Authorize</h3>

                <p>
                  Backend authentication and RBAC determine which data can be
                  used for the request.
                </p>
              </article>

              <article className="process-card">
                <span className="process-number">04</span>

                <div className="process-icon">
                  <Icon name="chart" size={21} />
                </div>

                <h3>Calculate</h3>

                <p>
                  Deterministic logic calculates the answer from the authorized
                  database records.
                </p>
              </article>

              <article className="process-card">
                <span className="process-number">05</span>

                <div className="process-icon">
                  <Icon name="receipt" size={21} />
                </div>

                <h3>Prove</h3>

                <p>
                  Source rows and an audit reference show where the result
                  came from.
                </p>
              </article>
            </div>
          </div>
        </section>

        {/* =====================================================
            SECURITY
            ===================================================== */}
        <section
          id="security"
          className="landing-section security-section"
        >
          <div className="landing-container security-grid">
            <div className="security-copy">
              <span className="landing-eyebrow">
                Security first
              </span>

              <h2>
                AI can understand the question.
                <span> It does not decide the number.</span>
              </h2>

              <p>
                L.E.D.G.E.R. keeps intelligence and authority separate. The
                AI layer interprets intent, while backend security controls
                access and deterministic logic produces the financial result.
              </p>

              <div className="security-points">
                <div>
                  <span className="security-check">
                    <Icon name="check" size={14} />
                  </span>

                  <div>
                    <strong>Authentication</strong>
                    <p>
                      Every request is tied to an authenticated session.
                    </p>
                  </div>
                </div>

                <div>
                  <span className="security-check">
                    <Icon name="check" size={14} />
                  </span>

                  <div>
                    <strong>Role-based access</strong>
                    <p>
                      Employees, Managers and Admins receive different
                      data scopes.
                    </p>
                  </div>
                </div>

                <div>
                  <span className="security-check">
                    <Icon name="check" size={14} />
                  </span>

                  <div>
                    <strong>Traceable results</strong>
                    <p>
                      Results can expose the source rows and audit reference
                      behind the answer.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="security-visual">
              <div className="security-panel">
                <div className="security-panel-header">
                  <span>
                    <i />
                    Secure query pipeline
                  </span>

                  <span className="security-live">
                    ACTIVE
                  </span>
                </div>

                <div className="security-flow">
                  <div className="security-node">
                    <span className="security-node-icon">
                      <Icon name="search" size={17} />
                    </span>

                    <div>
                      <strong>Natural language</strong>
                      <small>“What did we spend?”</small>
                    </div>
                  </div>

                  <div className="flow-line" />

                  <div className="security-node">
                    <span className="security-node-icon">
                      <Icon name="shield" size={17} />
                    </span>

                    <div>
                      <strong>Authorization</strong>
                      <small>Authenticated scope</small>
                    </div>
                  </div>

                  <div className="flow-line" />

                  <div className="security-node">
                    <span className="security-node-icon">
                      <Icon name="chart" size={17} />
                    </span>

                    <div>
                      <strong>Calculation</strong>
                      <small>Deterministic result</small>
                    </div>
                  </div>

                  <div className="flow-line" />

                  <div className="security-node">
                    <span className="security-node-icon">
                      <Icon name="check" size={17} />
                    </span>

                    <div>
                      <strong>Evidence</strong>
                      <small>Source + audit reference</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* =====================================================
            FEATURES
            ===================================================== */}
        <section
          id="features"
          className="landing-section features-section"
        >
          <div className="landing-container">
            <div className="section-heading centered">
              <span className="landing-eyebrow">
                Built for financial clarity
              </span>

              <h2>
                Everything you need to
                <span> understand the numbers.</span>
              </h2>

              <p>
                A focused workspace for querying, analyzing and managing
                financial information securely.
              </p>
            </div>

            <div className="features-grid">
              <article className="feature-card feature-card-large">
                <div className="feature-icon">
                  <Icon name="search" size={21} />
                </div>

                <h3>Natural-language financial search</h3>

                <p>
                  Ask questions using normal language instead of learning
                  complex reporting tools or query syntax.
                </p>

                <div className="feature-example">
                  <span>Try asking</span>
                  <strong>
                    “How much did we spend on Travel?”
                  </strong>
                </div>
              </article>

              <article className="feature-card">
                <div className="feature-icon">
                  <Icon name="chart" size={21} />
                </div>

                <h3>Analytics</h3>

                <p>
                  Explore spending patterns, categories and financial
                  summaries from authorized data.
                </p>
              </article>

              <article className="feature-card">
                <div className="feature-icon">
                  <Icon name="shield" size={21} />
                </div>

                <h3>RBAC</h3>

                <p>
                  Data visibility follows the user's authenticated role and
                  organizational scope.
                </p>
              </article>

              <article className="feature-card">
                <div className="feature-icon">
                  <Icon name="receipt" size={21} />
                </div>

                <h3>Evidence</h3>

                <p>
                  Inspect source records and audit references behind financial
                  answers.
                </p>
              </article>

              <article className="feature-card">
                <div className="feature-icon">
                  <Icon name="receipt" size={21} />
                </div>

                <h3>Expense management</h3>

                <p>
                  Add expenses through the authenticated workspace and keep
                  financial data connected to the platform.
                </p>
              </article>
            </div>
          </div>
        </section>

        {/* =====================================================
            CTA
            ===================================================== */}
        <section
          id="get-started"
          className="landing-cta-section"
        >
          <div className="landing-container">
            <div className="landing-cta">
              <div>
                <span className="landing-eyebrow">
                  Ready to explore?
                </span>

                <h2>
                  Ask better questions.
                  <span> Trust the answer.</span>
                </h2>

                <p>
                  Enter your secure L.E.D.G.E.R. workspace and start querying
                  your financial data.
                </p>
              </div>

              <button
                className="landing-button cta-button"
                onClick={handleGetStarted}
              >
                Enter L.E.D.G.E.R.
                <Icon name="arrow" size={17} />
              </button>
            </div>
          </div>
        </section>
      </main>

      {/* =====================================================
          FOOTER
          ===================================================== */}
      <footer className="landing-footer">
        <div className="landing-container footer-inner">
          <div>
            <strong>L.E.D.G.E.R.</strong>

            <span>
              Language-Enabled Data Governance & Expense Resolution
            </span>
          </div>

          <p>
            Evidence-backed financial intelligence.
          </p>

          <span>
            © 2026 L.E.D.G.E.R.
          </span>
        </div>
      </footer>
    </div>
  );
}