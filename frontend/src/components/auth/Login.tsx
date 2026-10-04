import { useState, type FormEvent } from "react";
import { Brand } from "../common/Brand";

type LoginProps = { onLogin: (email: string, password: string) => Promise<boolean> };

export function Login({ onLogin }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { if (!await onLogin(email, password)) setError("Invalid email or password."); }
    finally { setBusy(false); }
  }
  return <main className="login-page">
    <section className="login-story"><Brand light /><div className="story-content"><div className="eyebrow light">Evidence-backed analytics</div><h1>Clarity for every<br />financial decision.</h1><p>Ask questions in plain language. Review transparent answers grounded in authorized transaction data.</p><div className="trust-list"><div>Traceable results</div><div>Deterministic calculations</div><div>Database-backed access controls</div></div></div><p className="story-foot">Financial intelligence, explained.</p></section>
    <section className="login-panel"><form className="login-card" onSubmit={submit}>
      <div className="mobile-brand"><Brand /></div><div className="login-heading"><h2>Welcome back</h2><p>Sign in to your financial workspace</p></div>
      {error && <div className="login-error" role="alert">{error}</div>}
      <label className="field"><span>Email</span><input type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@example.com" /></label>
      <label className="field"><span>Password</span><input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" /></label>
      <button className="primary full ledger-login-button" type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in to LEDGER"}</button>
      <p className="prototype-note">Use a database-backed demo account. Accounts cannot be created from this screen.</p>
    </form></section>
  </main>;
}
