import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from "react";
import {
  createAdminUser,
  getAdminOptions,
  getAdminSummary,
  getAdminUsers,
  getRecentAudits,
  updateAdminCostCentre,
  updateAdminRole,
  type AdminOptions,
  type AdminSummary,
  type AdminUser
} from "../../services/api";
import { formatMoney } from "../../utils/formatters";
import "./admin.css";

type Page = "dashboard" | "users" | "audit" | "admin";

const iconPaths: Record<string, ReactNode> = {
  grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
  users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></>,
  shield: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>,
  logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5M21 12H9"/></>,
  search: <><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></>,
  plus: <><path d="M12 5v14M5 12h14"/></>,
  chevron: <path d="m9 18 6-6-6-6"/>,
  close: <><path d="m18 6-12 12M6 6l12 12"/></>,
  menu: <><path d="M4 6h16M4 12h16M4 18h16"/></>,
  dots: <><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></>,
  arrow: <><path d="M5 12h14M13 6l6 6-6 6"/></>,
  lock: <><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></>,
  alert: <><path d="M10.3 2.9 1.8 17a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 2.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/></>,
  refresh: <><path d="M20 11a8 8 0 1 0-2.3 5.7L20 14"/><path d="M20 6v5h-5"/></>,
  mail: <><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></>,
  check: <path d="m5 12 4 4L19 6"/>,
  sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41"/></>,
  moon: <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z"/>,
  loader: <path d="M21 12a9 9 0 1 1-6.2-8.56"/>,
  audit: <><path d="M4 19V5a2 2 0 0 1 2-2h9l5 5v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z"/><path d="M14 3v6h6M8 13h8M8 17h5"/></>,
};

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {iconPaths[name]}
    </svg>
  );
}

function Logo() {
  return (
    <div className="brand">
      <div className="brand-mark">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <div>
        <strong>L.E.D.G.E.R.</strong>
        <small>ADMIN PORTAL</small>
      </div>
    </div>
  );
}

function Button({
  children,
  variant = "primary",
  onClick,
  icon,
  type = "button",
  loading = false,
  disabled = false,
}: {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  onClick?: () => void;
  icon?: string;
  type?: "button" | "submit";
  loading?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      type={type}
      className={`button ${variant} ${loading ? "is-loading" : ""}`}
      onClick={onClick}
      disabled={disabled || loading}
      aria-busy={loading}
    >
      {loading ? <Icon name="loader" size={16} /> : icon && <Icon name={icon} size={16} />}
      <span>{children}</span>
    </button>
  );
}

function AdminSidebar({
  page,
  setPage,
  open,
  close,
}: {
  page: Page;
  setPage: (p: Page) => void;
  open: boolean;
  close: () => void;
}) {
  const nav = [
    { id: "dashboard" as Page, label: "Dashboard", icon: "grid" },
    { id: "users" as Page, label: "User Management", icon: "users" },
    { id: "audit" as Page, label: "Audit Log", icon: "audit" },
    { id: "admin" as Page, label: "Admin & RBAC", icon: "shield" },
  ];
  return (
    <>
      {open && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={close} />}
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <Logo />
        <nav>
          {nav.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${page === item.id ? "active" : ""}`}
              onClick={() => {
                setPage(item.id);
                close();
              }}
            >
              <Icon name={item.icon} size={20} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="system-pill">
            <span className="dot green"></span>
            <span>FastAPI Backend Connected</span>
          </div>
        </div>
      </aside>
    </>
  );
}

export function AdminPortal({ onIdentityChanged }: { onIdentityChanged?: () => Promise<void> }) {
  const [page, setPage] = useState<Page>("dashboard");
  const [theme, setTheme] = useState<"dark" | "light">("light");
  const [navOpen, setNavOpen] = useState(false);

  // Real backend data states
  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [options, setOptions] = useState<AdminOptions>({ roles: [], cost_centres: [] });
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Filter & Form states
  const [search, setSearch] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [filterCentre, setFilterCentre] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "Employee",
    cost_centre: "",
  });

  const toggleTheme = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  const loadUsers = useCallback(async () => {
    try {
      const data = await getAdminUsers({ search, role: filterRole, cost_centre: filterCentre });
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users from backend.");
    }
  }, [search, filterRole, filterCentre]);

  const loadAudits = useCallback(async () => {
    try {
      const logs = await getRecentAudits(50);
      setAuditLogs(logs);
    } catch (err) {
      // audit endpoint might return 403 if not admin
    }
  }, []);

  const reloadAll = useCallback(async () => {
    setError("");
    try {
      const [s, o] = await Promise.all([getAdminSummary(), getAdminOptions()]);
      setSummary(s);
      setOptions(o);
      await Promise.all([loadUsers(), loadAudits()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not initialize Admin Portal.");
    }
  }, [loadUsers, loadAudits]);

  useEffect(() => {
    void reloadAll();
  }, [reloadAll]);

  useEffect(() => {
    if (!form.cost_centre && options.cost_centres.length > 0) {
      setForm((cur) => ({ ...cur, cost_centre: options.cost_centres[0] }));
    }
  }, [options.cost_centres, form.cost_centre]);

  async function handleAction(op: () => Promise<unknown>, successMsg: string) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await op();
      await reloadAll();
      if (onIdentityChanged) await onIdentityChanged();
      setNotice(successMsg);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateUser(e: FormEvent) {
    e.preventDefault();
    await handleAction(
      () => createAdminUser(form),
      `User ${form.email} was successfully created in the SQLite database.`
    );
    setForm((cur) => ({ ...cur, name: "", email: "", password: "" }));
    setModalOpen(false);
  }

  return (
    <div className="admin-portal" data-theme={theme}>
      <AdminSidebar page={page} setPage={setPage} open={navOpen} close={() => setNavOpen(false)} />

      <div className="app-main">
        {/* Header Bar */}
        <header className="topbar">
          <div className="topbar-left">
            <button className="icon-button mobile-only" onClick={() => setNavOpen(true)} aria-label="Open navigation">
              <Icon name="menu" size={20} />
            </button>
            <div className="page-title">
              <h1>{page === "dashboard" ? "System Dashboard" : page === "users" ? "User Management" : page === "audit" ? "Audit Trail" : "Admin & RBAC Controls"}</h1>
              <span className="badge green">RBAC Governed</span>
            </div>
          </div>
          <div className="topbar-right">
            <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
              <Icon name={theme === "dark" ? "sun" : "moon"} size={18} />
            </button>
          </div>
        </header>

        {/* Global Notifications */}
        {error && (
          <div className="banner error-banner">
            <Icon name="alert" size={18} />
            <span>{error}</span>
          </div>
        )}
        {notice && (
          <div className="banner success-banner">
            <Icon name="check" size={18} />
            <span>{notice}</span>
          </div>
        )}

        {/* Content Area */}
        <div className="admin-content">
          {/* TAB 1: DASHBOARD */}
          {page === "dashboard" && (
            <div className="tab-pane">
              <div className="stats-grid">
                <article className="stat-card">
                  <div className="stat-icon blue">
                    <Icon name="users" size={24} />
                  </div>
                  <div className="stat-info">
                    <small>Registered Accounts</small>
                    <strong>{summary ? summary.user_count : "—"}</strong>
                    <span className="stat-meta">
                      {summary?.users_by_role.map((r) => `${r.role}: ${r.count}`).join(" · ") || "Loading users..."}
                    </span>
                  </div>
                </article>

                <article className="stat-card green">
                  <div className="stat-icon green">
                    <Icon name="grid" size={24} />
                  </div>
                  <div className="stat-info">
                    <small>Total Expenses Stored</small>
                    <strong>{summary ? summary.expense_count : "—"}</strong>
                    <span className="stat-meta">Database expense records</span>
                  </div>
                </article>

                {summary?.spend_by_currency.map((sc) => (
                  <article className="stat-card purple" key={sc.currency}>
                    <div className="stat-icon purple">
                      <Icon name="shield" size={24} />
                    </div>
                    <div className="stat-info">
                      <small>Total Spend ({sc.currency})</small>
                      <strong>{formatMoney(sc.amount, sc.currency)}</strong>
                      <span className="stat-meta">Real database sum</span>
                    </div>
                  </article>
                ))}
              </div>

              <div className="panels-row">
                <section className="admin-card">
                  <div className="card-header">
                    <h2>Live Backend Environment</h2>
                    <Button variant="ghost" icon="refresh" onClick={() => void reloadAll()}>
                      Refresh
                    </Button>
                  </div>
                  <div className="system-health-list">
                    <div className="health-item">
                      <span>SQLite Database</span>
                      <span className="badge green">Connected (`data/demo_ledger.db`)</span>
                    </div>
                    <div className="health-item">
                      <span>RBAC Matrix</span>
                      <span className="badge green">Server Enforced (Employee / Manager / Admin)</span>
                    </div>
                    <div className="health-item">
                      <span>Audit Trail Engine</span>
                      <span className="badge green">Active (`data/audit.db`)</span>
                    </div>
                    <div className="health-item">
                      <span>Query Compiler</span>
                      <span className="badge green">Deterministic Parameterized SQL</span>
                    </div>
                  </div>
                </section>

                <section className="admin-card">
                  <div className="card-header">
                    <h2>Recent Audit Logs</h2>
                    <Button variant="ghost" onClick={() => setPage("audit")}>
                      View All
                    </Button>
                  </div>
                  <div className="mini-audit-list">
                    {auditLogs.slice(0, 5).map((log) => (
                      <div className="audit-mini-item" key={log.audit_id || log.query_id}>
                        <div className="audit-mini-main">
                          <strong>{log.natural_query || "Query Execution"}</strong>
                          <small>
                            User: {log.user_id} · Scope: {log.cost_centre || "Org"} · {log.timestamp}
                          </small>
                        </div>
                        <span className="badge blue">{log.intent || "Executed"}</span>
                      </div>
                    ))}
                    {auditLogs.length === 0 && <p className="empty-text">No audit logs recorded yet.</p>}
                  </div>
                </section>
              </div>
            </div>
          )}

          {/* TAB 2: USER MANAGEMENT */}
          {page === "users" && (
            <div className="tab-pane">
              <div className="toolbar">
                <div className="search-box">
                  <Icon name="search" size={18} />
                  <input
                    type="text"
                    placeholder="Search by name, email, or User ID..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
                <div className="filters-group">
                  <select value={filterRole} onChange={(e) => setFilterRole(e.target.value)}>
                    <option value="">All Roles</option>
                    {options.roles.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>

                  <select value={filterCentre} onChange={(e) => setFilterCentre(e.target.value)}>
                    <option value="">All Cost Centres</option>
                    {options.cost_centres.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>

                  <Button icon="plus" onClick={() => setModalOpen(true)}>
                    Add Account
                  </Button>
                </div>
              </div>

              <div className="table-card">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>User ID / Name</th>
                      <th>Email</th>
                      <th>Assigned Role</th>
                      <th>Cost Centre</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.user_id}>
                        <td>
                          <div className="user-cell">
                            <strong>{u.name}</strong>
                            <small>{u.user_id}</small>
                          </div>
                        </td>
                        <td>{u.email}</td>
                        <td>
                          <select
                            className="role-select"
                            value={u.role}
                            disabled={busy}
                            onChange={(e) =>
                              void handleAction(
                                () => updateAdminRole(u.user_id, e.target.value),
                                `Role updated to ${e.target.value} for ${u.email}`
                              )
                            }
                          >
                            {options.roles.map((r) => (
                              <option key={r} value={r}>
                                {r}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td>
                          <select
                            className="centre-select"
                            value={u.cost_centre}
                            disabled={busy}
                            onChange={(e) =>
                              void handleAction(
                                () => updateAdminCostCentre(u.user_id, e.target.value),
                                `Cost centre updated to ${e.target.value} for ${u.email}`
                              )
                            }
                          >
                            {options.cost_centres.map((c) => (
                              <option key={c} value={c}>
                                {c}
                              </option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    ))}
                    {users.length === 0 && (
                      <tr>
                        <td colSpan={4} className="table-empty">
                          No database accounts match the specified criteria.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: AUDIT LOG */}
          {page === "audit" && (
            <div className="tab-pane">
              <div className="card-header">
                <div>
                  <h2>System Audit Trail</h2>
                  <p>All natural-language queries and calculated results are logged with user authorization context.</p>
                </div>
                <Button variant="ghost" icon="refresh" onClick={() => void loadAudits()}>
                  Reload Logs
                </Button>
              </div>

              <div className="table-card">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>User ID / Scope</th>
                      <th>Natural Language Query</th>
                      <th>Intent</th>
                      <th>Result / Source Rows</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map((log) => (
                      <tr key={log.audit_id || log.query_id}>
                        <td className="timestamp-cell">{log.timestamp}</td>
                        <td>
                          <strong>{log.user_id}</strong>
                          <br />
                          <small className="badge-sub">{log.cost_centre || "Org Scope"}</small>
                        </td>
                        <td className="query-cell">"{log.natural_query}"</td>
                        <td>
                          <span className="badge blue">{log.intent}</span>
                        </td>
                        <td>
                          {log.calculation_result !== undefined && log.calculation_result !== null ? (
                            <strong>
                              {typeof log.calculation_result === "number"
                                ? formatMoney(log.calculation_result, log.currency || "INR")
                                : log.calculation_result}
                            </strong>
                          ) : (
                            <small>Execution Recorded</small>
                          )}
                          <br />
                          <small>{log.source_row_count || 0} source rows</small>
                        </td>
                      </tr>
                    ))}
                    {auditLogs.length === 0 && (
                      <tr>
                        <td colSpan={5} className="table-empty">
                          No audit log entries recorded in SQLite `data/audit.db`.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: ADMIN / RBAC SETTINGS */}
          {page === "admin" && (
            <div className="tab-pane">
              <div className="admin-card">
                <h2>Role-Based Access Control (RBAC) Matrix</h2>
                <p>The backend enforces non-bypassable scope isolation for every calculation and query execution.</p>

                <div className="rbac-grid">
                  <div className="rbac-card">
                    <span className="badge green">Employee</span>
                    <h3>Individual Scope</h3>
                    <p>Can query and submit only their own personal expense records (`user_id`). Cannot access organization or cost-centre aggregates.</p>
                  </div>

                  <div className="rbac-card">
                    <span className="badge blue">Manager</span>
                    <h3>Cost Centre Scope</h3>
                    <p>Can query expenses and budget burn for their assigned cost centre (e.g. `CC-TECH`). Access outside cost centre is blocked server-side.</p>
                  </div>

                  <div className="rbac-card">
                    <span className="badge purple">Admin</span>
                    <h3>Organization Scope</h3>
                    <p>Has full organization-wide visibility across all cost centres. Authorized to provision accounts, modify roles, and view global audit logs.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CREATE USER MODAL */}
      {modalOpen && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h2>Provision New Account</h2>
              <button className="icon-button" onClick={() => setModalOpen(false)}>
                <Icon name="close" size={20} />
              </button>
            </div>
            <form onSubmit={(e) => void handleCreateUser(e)}>
              <div className="form-group">
                <label>Full Name</label>
                <input
                  required
                  maxLength={100}
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Alex Morgan"
                />
              </div>

              <div className="form-group">
                <label>Email Address</label>
                <input
                  required
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="alex@example.com"
                />
              </div>

              <div className="form-group">
                <label>Initial Password (min 12 characters)</label>
                <input
                  required
                  minLength={12}
                  maxLength={72}
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="••••••••••••"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Role</label>
                  <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                    {options.roles.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Cost Centre</label>
                  <select
                    required
                    value={form.cost_centre}
                    onChange={(e) => setForm({ ...form, cost_centre: e.target.value })}
                  >
                    {options.cost_centres.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="modal-actions">
                <Button variant="secondary" onClick={() => setModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" loading={busy}>
                  Create User
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
