import { FormEvent, useState } from "react";
import { Icon } from "../common/Icon";
import { GoogleLogo } from "../common/GoogleLogo";
import { Button } from "../common/Button";
import { Brand } from "../common/Brand";

type LoginProps = {
  onLogin: () => void;
  initialView?: "login" | "signup";
  onView?: (view: "login" | "signup") => void;
};

export function Login({
  onLogin,
  initialView = "login",
  onView,
}: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);

  const [view, setView] = useState<
    "login" | "signup" | "success"
  >(initialView);

  const [signup, setSignup] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [signupErrors, setSignupErrors] = useState<
    Record<string, string>
  >({});

  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleError, setGoogleError] = useState("");

  function submit(event: FormEvent) {
    event.preventDefault();

    if (!email.trim() || !password.trim()) {
      setError(true);
      return;
    }

    onLogin();
  }

  function updateSignup(
    field: keyof typeof signup,
    value: string
  ) {
    setSignup((current) => ({
      ...current,
      [field]: value,
    }));

    setSignupErrors((current) => {
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  function submitSignup(event: FormEvent) {
    event.preventDefault();

    const nextErrors: Record<string, string> = {};

    if (!signup.name.trim()) {
      nextErrors.name = "Please enter your full name.";
    }

    if (
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
        signup.email.trim()
      )
    ) {
      nextErrors.email =
        "Please enter a valid email address.";
    }

    if (!signup.password) {
      nextErrors.password = "Please enter a password.";
    } else if (signup.password.length < 8) {
      nextErrors.password =
        "Password must be at least 8 characters.";
    }

    if (signup.confirmPassword !== signup.password) {
      nextErrors.confirmPassword =
        "Passwords do not match.";
    }

    setSignupErrors(nextErrors);

    if (Object.keys(nextErrors).length === 0) {
      setView("success");
    }
  }

  function showLogin() {
    setView("login");
    setSignupErrors({});
    setGoogleError("");
    onView?.("login");
  }

  function showSignup() {
    setView("signup");
    setError(false);
    setGoogleError("");
    onView?.("signup");
  }

  function continueWithGoogle() {
    setGoogleError("");

    if (!window.navigator.onLine) {
      setGoogleError(
        "Google sign-in is unavailable while you’re offline. Please try again when connected."
      );
      return;
    }

    setGoogleLoading(true);

    window.setTimeout(() => {
      setGoogleLoading(false);
      onLogin();
    }, 700);
  }

  return (
    <main className="login-page">
      <section className="login-story">
        <Brand light />

        <div className="story-content">
          <div className="eyebrow light">
            <Icon name="shield" size={16} />
            Evidence-backed analytics
          </div>

          <h1>
            Clarity for every
            <br />
            financial decision.
          </h1>

          <p>
            Ask questions in plain language. Get transparent
            answers grounded in your transaction data.
          </p>

          <div className="trust-list">
            <div>
              <Icon name="check" />
              <span>
                <strong>Traceable results</strong>
                <small>
                  Every answer links to source transactions
                </small>
              </span>
            </div>

            <div>
              <Icon name="check" />
              <span>
                <strong>Clear calculations</strong>
                <small>
                  See exactly how each result was derived
                </small>
              </span>
            </div>

            <div>
              <Icon name="check" />
              <span>
                <strong>Built for confidence</strong>
                <small>
                  No guessing, no hidden financial logic
                </small>
              </span>
            </div>
          </div>
        </div>

        <p className="story-foot">
          Financial intelligence, explained.
        </p>
      </section>

      <section className="login-panel">
        {view === "login" && (
          <form
            className="login-card"
            onSubmit={submit}
          >
            <div className="mobile-brand">
              <Brand />
            </div>

            <div className="login-heading">
              <span className="login-icon">
                <Icon name="user" />
              </span>

              <h2>Welcome back</h2>

              <p>
                Sign in to your financial workspace
              </p>
            </div>

            {error && (
              <div
                className="login-error"
                role="alert"
              >
                <Icon name="warning" size={18} />

                <span>
                  <strong>Unable to sign in</strong>
                  Please enter both your email and
                  password.
                </span>
              </div>
            )}

            <label className="field">
              <span>Email or username</span>

              <input
                type="text"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setError(false);
                }}
                placeholder="alex@example.com"
              />
            </label>

            <label className="field">
              <span className="label-row">
                <span>Password</span>
                <span className="text-link">
                  Forgot password?
                </span>
              </span>

              <input
                type="password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setError(false);
                }}
                placeholder="Enter your password"
              />
            </label>

            <Button
              type="submit"
              className="primary full"
            >
              Sign in to LEDGER
              <Icon name="arrow" size={18} />
            </Button>

            <div className="auth-divider">
              <span>OR</span>
            </div>

            <Button
              className="google-auth full"
              onClick={continueWithGoogle}
              disabled={googleLoading}
            >
              <GoogleLogo />

              {googleLoading
                ? "Connecting to Google…"
                : "Continue with Google"}
            </Button>

            {googleError && (
              <p
                className="google-error"
                role="alert"
              >
                <Icon name="warning" size={14} />
                {googleError}
              </p>
            )}

            <p className="auth-switch">
              New user?{" "}
              <button
                type="button"
                onClick={showSignup}
              >
                Sign Up
              </button>
            </p>

            <p className="prototype-note">
              <Icon name="info" size={15} />
              Prototype only — use any email and password
            </p>
          </form>
        )}

        {view === "signup" && (
          <form
            className="login-card signup-card"
            onSubmit={submitSignup}
            noValidate
          >
            <div className="mobile-brand">
              <Brand />
            </div>

            <div className="login-heading">
              <span className="login-icon">
                <Icon name="user" />
              </span>

              <h2>Create your account</h2>

              <p>
                Sign up to start managing and analyzing
                your finances.
              </p>
            </div>

            <label
              className={`field ${
                signupErrors.name
                  ? "field-invalid"
                  : ""
              }`}
            >
              <span>Full Name</span>

              <input
                type="text"
                value={signup.name}
                onChange={(event) =>
                  updateSignup(
                    "name",
                    event.target.value
                  )
                }
                placeholder="Alex Kumar"
                aria-invalid={Boolean(
                  signupErrors.name
                )}
              />

              {signupErrors.name && (
                <small className="field-error">
                  <Icon name="warning" size={13} />
                  {signupErrors.name}
                </small>
              )}
            </label>

            <label
              className={`field ${
                signupErrors.email
                  ? "field-invalid"
                  : ""
              }`}
            >
              <span>Email Address</span>

              <input
                type="email"
                value={signup.email}
                onChange={(event) =>
                  updateSignup(
                    "email",
                    event.target.value
                  )
                }
                placeholder="alex@example.com"
                aria-invalid={Boolean(
                  signupErrors.email
                )}
              />

              {signupErrors.email && (
                <small className="field-error">
                  <Icon name="warning" size={13} />
                  {signupErrors.email}
                </small>
              )}
            </label>

            <label
              className={`field ${
                signupErrors.password
                  ? "field-invalid"
                  : ""
              }`}
            >
              <span>Password</span>

              <input
                type="password"
                value={signup.password}
                onChange={(event) =>
                  updateSignup(
                    "password",
                    event.target.value
                  )
                }
                placeholder="Minimum 8 characters"
                aria-invalid={Boolean(
                  signupErrors.password
                )}
              />

              {signupErrors.password && (
                <small className="field-error">
                  <Icon name="warning" size={13} />
                  {signupErrors.password}
                </small>
              )}
            </label>

            <label
              className={`field ${
                signupErrors.confirmPassword
                  ? "field-invalid"
                  : ""
              }`}
            >
              <span>Confirm Password</span>

              <input
                type="password"
                value={signup.confirmPassword}
                onChange={(event) =>
                  updateSignup(
                    "confirmPassword",
                    event.target.value
                  )
                }
                placeholder="Re-enter your password"
                aria-invalid={Boolean(
                  signupErrors.confirmPassword
                )}
              />

              {signupErrors.confirmPassword && (
                <small className="field-error">
                  <Icon name="warning" size={13} />
                  {signupErrors.confirmPassword}
                </small>
              )}
            </label>

            <Button
              type="submit"
              className="primary full"
            >
              Create Account
              <Icon name="arrow" size={18} />
            </Button>

            <div className="auth-divider">
              <span>OR</span>
            </div>

            <Button
              className="google-auth full"
              onClick={continueWithGoogle}
              disabled={googleLoading}
            >
              <GoogleLogo />

              {googleLoading
                ? "Connecting to Google…"
                : "Continue with Google"}
            </Button>

            {googleError && (
              <p
                className="google-error"
                role="alert"
              >
                <Icon name="warning" size={14} />
                {googleError}
              </p>
            )}

            <p className="auth-switch">
              Already have an account?{" "}
              <button
                type="button"
                onClick={showLogin}
              >
                Log In
              </button>
            </p>
          </form>
        )}

        {view === "success" && (
          <section
            className="login-card signup-success"
            aria-live="polite"
          >
            <div className="mobile-brand">
              <Brand />
            </div>

            <span className="success-icon">
              <Icon name="check" size={28} />
            </span>

            <p className="section-kicker">
              Registration complete
            </p>

            <h2>Account created successfully</h2>

            <p>
              Your LEDGER workspace is ready. You can
              continue to the dashboard or return to the
              login screen.
            </p>

            <Button
              className="primary full"
              onClick={onLogin}
            >
              Continue to Dashboard
              <Icon name="arrow" size={18} />
            </Button>

            <Button
              className="full"
              onClick={showLogin}
            >
              Return to Login
            </Button>
          </section>
        )}

        <p className="login-footer">
          Protected financial workspace · UI demonstration
        </p>
      </section>
    </main>
  );
}