import { useCallback, useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { createUser, getAuditLog, getAuditLogs, getUsers, isAdminApiConfigured, updateUser } from "../../api/admin";
import { mockAuditLogs, mockUsers } from "../../data/adminMockData";
import "./admin.css";
import type { AdminRole as Role, AdminUser as User, AuditLog, AuthenticatedUser, CreateUserInput, UpdateUserInput } from "../../types/admin";

type Page = "dashboard" | "users" | "audit" | "admin";

const costCentres = ["All Cost Centres", "CC-TECH", "CC-FINANCE", "CC-HR", "CC-SALES", "CC-MARKETING"];

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
  return <svg className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{iconPaths[name]}</svg>;
}

function Logo() {
  return <div className="brand"><div className="brand-mark"><span></span><span></span><span></span></div><div><strong>L.E.D.G.E.R.</strong><small>ADMIN PORTAL</small></div></div>;
}

function Button({ children, variant = "primary", onClick, icon, type = "button", loading = false, disabled = false }: { children: ReactNode; variant?: "primary" | "secondary" | "ghost" | "danger"; onClick?: () => void; icon?: string; type?: "button" | "submit"; loading?: boolean; disabled?: boolean }) {
  return <button type={type} className={`button ${variant} ${loading ? "is-loading" : ""}`} onClick={onClick} disabled={disabled || loading} aria-busy={loading}>{loading ? <Icon name="loader" size={16}/> : icon && <Icon name={icon} size={16}/>}<span>{children}</span></button>;
}

function AdminSidebar({ page, setPage, open, close }: { page: Page; setPage: (p: Page) => void; open: boolean; close: () => void }) {
  const nav = [{ id: "dashboard" as Page, label: "Dashboard", icon: "grid" }, { id: "users" as Page, label: "User Management", icon: "users" }, { id: "audit" as Page, label: "Audit Log", icon: "audit" }, { id: "admin" as Page, label: "Admin", icon: "shield" }];
  return <>
    {open && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={close}/>}
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <Logo />
      <div className="nav-label">WORKSPACE</div>
      <nav>{nav.map(item => <button key={item.id} className={`nav-item ${page === item.id ? "active" : ""}`} onClick={() => { setPage(item.id); close(); }}><Icon name={item.icon}/><span>{item.label}</span>{page === item.id && <Icon name="chevron" size={15}/>}</button>)}</nav>
      <div className="sidebar-foot"><div className="security-note"><Icon name="lock" size={16}/><div><b>Secure admin session</b><small>Protected by role-based access</small></div></div><button className="nav-item"><Icon name="logout"/><span>Log out</span></button></div>
    </aside>
  </>;
}

function ThemeSwitcher({ theme, toggle }: { theme: "dark" | "light"; toggle: () => void }) {
  return <button className="theme-switcher" onClick={toggle} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`} title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}><span className={theme === "light" ? "active" : ""}><Icon name="sun" size={14}/></span><span className={theme === "dark" ? "active" : ""}><Icon name="moon" size={14}/></span></button>;
}

function AdminHeader({ toggleNav, theme, toggleTheme, user }: { toggleNav: () => void; theme: "dark" | "light"; toggleTheme: () => void; user?: AuthenticatedUser | null }) {
  const name = user?.name || "Admin Name";
  return <header className="topbar"><button className="mobile-menu" onClick={toggleNav} aria-label="Open navigation"><Icon name="menu"/></button><div className="topbar-context"><span>Organization</span><b>Ledger India Pvt. Ltd.</b></div><div className="header-actions"><ThemeSwitcher theme={theme} toggle={toggleTheme}/><div className="admin-profile"><div className="profile-copy"><b>{name}</b><span>{user ? `${user.role} · ${user.cost_centre}` : "Admin · Organization"}</span></div><div className="avatar">{initials(name)}</div></div></div></header>;
}

function AdminStatCard({ label, value, meta, icon }: { label: string; value: number; meta: string; icon: string }) {
  return <article className="stat-card"><div className="stat-top"><span>{label}</span><div className="stat-icon"><Icon name={icon}/></div></div><strong>{value}</strong><small><i></i>{meta}</small></article>;
}

function RoleBadge({ role }: { role: Role }) { return <span className={`badge role-${role.toLowerCase()}`}>{role}</span>; }
function CostCentreBadge({ value }: { value: string }) { return <span className="cost-badge">{value}</span>; }
function StatusBadge({ status }: { status: User["status"] | "Inactive" }) { return <span className={`status ${status.toLowerCase()}`}><i></i>{status}</span>; }

function AdminActivityList({ openAudit }: { openAudit: () => void }) {
  const activity = [
    ["Role updated", "Rahul Sharma", "Admin Name", "2 min ago"],
    ["New user created", "Priya Singh", "Admin Name", "15 min ago"],
    ["Access scope changed", "Shaurya Mehta", "Admin Name", "1 hr ago"],
  ];
  return <section className="panel activity-panel"><div className="section-head"><div><h2>Recent Activity</h2><p>Latest organization access changes</p></div><button className="text-button" onClick={openAudit}>View audit log <Icon name="arrow" size={14}/></button></div><div className="activity-table"><div className="table-head four"><span>Action</span><span>User</span><span>Changed by</span><span>Time</span></div>{activity.map((row, i) => <div className="activity-row" key={i}><div><span className="activity-dot"><Icon name={i === 1 ? "plus" : "shield"} size={14}/></span><b>{row[0]}</b></div><span>{row[1]}</span><span>{row[2]}</span><time>{row[3]}</time></div>)}</div></section>;
}

function Dashboard({ openAudit }: { openAudit: () => void }) {
  return <><PageTitle eyebrow="ADMIN OVERVIEW" title="L.E.D.G.E.R. Admin Portal" subtitle="Manage users, roles and organizational access."/>
    <div className="stats-grid"><AdminStatCard label="Total Users" value={110} meta="6 added this month" icon="users"/><AdminStatCard label="Employees" value={64} meta="58% of all users" icon="users"/><AdminStatCard label="Managers" value={23} meta="Across 5 cost centres" icon="shield"/><AdminStatCard label="Admins" value={23} meta="Organization-wide access" icon="lock"/></div>
    <section className="panel chart-panel"><div className="section-head"><div><h2>User Overview</h2><p>Users by role</p></div><span className="placeholder-label">DESIGN PLACEHOLDER</span></div><div className="role-chart"><div className="donut" aria-label="64 employees, 23 managers and 23 admins"><div><strong>110</strong><span>Total users</span></div></div><div className="chart-legend">{[["Employee", 64, "58%", "employee"], ["Manager", 23, "21%", "manager"], ["Admin", 23, "21%", "admin"]].map(item => <div className="legend-row" key={item[0]}><i className={`legend-dot ${item[3]}`}></i><span>{item[0]}</span><b>{item[1]}</b><small>{item[2]}</small></div>)}</div><div className="bar-chart">{[["Employee", 64], ["Manager", 23], ["Admin", 23]].map(item => <div className="bar-row" key={item[0]}><span>{item[0]}</span><div><i style={{ width: `${Number(item[1]) / 64 * 100}%` }}></i></div><b>{item[1]}</b></div>)}</div></div></section>
    <AdminActivityList openAudit={openAudit}/>
  </>;
}

function PageTitle({ eyebrow, title, subtitle, action }: { eyebrow?: string; title: string; subtitle: string; action?: ReactNode }) {
  return <div className="page-title"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h1>{title}</h1><p>{subtitle}</p></div>{action}</div>;
}

function SearchBar({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <label className="search"><Icon name="search"/><input value={value} onChange={e => onChange(e.target.value)} placeholder="Search users..." aria-label="Search users"/></label>;
}

function RoleFilter({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <label className="select-wrap"><span>Role</span><select value={value} onChange={e => onChange(e.target.value)}><option>All Roles</option><option>Employee</option><option>Manager</option><option>Admin</option></select></label>;
}

function CostCentreFilter({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <label className="select-wrap wide"><span>Cost Centre</span><select value={value} onChange={e => onChange(e.target.value)}>{costCentres.map(c => <option key={c}>{c}</option>)}</select></label>;
}

function UserRow({ user, edit, details }: { user: User; edit: () => void; details: () => void }) {
  return <tr><td><button className="user-cell" onClick={details}><span className="table-avatar">{initials(user.name)}</span><span><b>{user.name}</b><small>{user.id}</small></span></button></td><td className="email-cell">{user.email}</td><td><RoleBadge role={user.role}/></td><td><CostCentreBadge value={user.costCentre}/></td><td><StatusBadge status={user.status}/></td><td><button className="edit-btn" onClick={edit}>Edit</button><button className="dots-btn" aria-label={`More options for ${user.name}`}><Icon name="dots"/></button></td></tr>;
}

function UserTable({ data, edit, details }: { data: User[]; edit: (u: User) => void; details: (u: User) => void }) {
  return <div className="table-scroll"><table className="user-table"><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Cost Centre</th><th>Status</th><th>Actions</th></tr></thead><tbody>{data.map(user => <UserRow user={user} key={user.id} edit={() => edit(user)} details={() => details(user)}/>)}</tbody></table></div>;
}

function EmptyState({ clear }: { clear: () => void }) {
  return <div className="empty-state"><div className="state-icon"><Icon name="search"/></div><h3>No users found</h3><p>No users match your current filters.</p><Button variant="secondary" onClick={clear}>Clear filters</Button></div>;
}

function UserManagement({ users, isLoading, error, refresh, previewMode, openAdd, openEdit, openDetails }: { users: User[]; isLoading: boolean; error: string | null; refresh: () => void; previewMode: boolean; openAdd: () => void; openEdit: (u: User) => void; openDetails: (u: User) => void }) {
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("All Roles");
  const [cost, setCost] = useState("All Cost Centres");
  const filtered = useMemo(() => users.filter(u => (u.name + u.email).toLowerCase().includes(search.toLowerCase()) && (role === "All Roles" || u.role === role) && (cost === "All Cost Centres" || u.costCentre === cost)), [search, role, cost]);
  const clear = () => { setSearch(""); setRole("All Roles"); setCost("All Cost Centres"); };
  return <><PageTitle title="User Management" subtitle="Manage users, roles and access scopes." action={<Button icon="plus" onClick={openAdd}>Add User</Button>}/>
    <section className="panel users-panel"><div className="filter-bar"><SearchBar value={search} onChange={setSearch}/><div className="filter-group"><RoleFilter value={role} onChange={setRole}/><CostCentreFilter value={cost} onChange={setCost}/></div></div>
      {previewMode && <div className="preview-notice">Design preview data · Connect VITE_API_BASE_URL for live users</div>}
      {isLoading ? <div className="table-state"><LoadingState variant="table"/><span>Loading users...</span></div> : error ? <div className="empty-state"><div className="state-icon danger"><Icon name="refresh"/></div><h3>Unable to load users</h3><p>{error}</p><Button variant="secondary" icon="refresh" onClick={refresh}>Try again</Button></div> : filtered.length ? <><UserTable data={filtered} edit={openEdit} details={openDetails}/><div className="table-foot"><span>Showing <b>{filtered.length}</b> of <b>{users.length}</b> users</span><div><button disabled>Previous</button><button className="page-active">1</button><button disabled>Next</button></div></div></> : <EmptyState clear={clear}/>}
    </section>
  </>;
}

function ModalShell({ children, onClose, size = "normal" }: { children: ReactNode; onClose: () => void; size?: "normal" | "small" }) {
  return <div className="modal-layer" role="presentation"><button className="modal-backdrop" onClick={onClose} aria-label="Close modal"/><div className={`modal ${size}`} role="dialog" aria-modal="true">{children}</div></div>;
}

function ModalHeader({ title, subtitle, onClose }: { title: string; subtitle: string; onClose: () => void }) {
  return <div className="modal-head"><div><h2>{title}</h2><p>{subtitle}</p></div><button className="close-btn" onClick={onClose} aria-label="Close"><Icon name="close"/></button></div>;
}

function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) { return <label className="field"><span>{label}</span>{children}{error && <small className="field-error">{error}</small>}</label>; }

function AddUserModal({ close, submit }: { close: () => void; submit: (data: CreateUserInput) => Promise<void> }) {
  const [form, setForm] = useState<CreateUserInput>({ name: "", email: "", password: "", role: "Employee", cost_centre: "CC-MARKETING" });
  const [errors, setErrors] = useState<Partial<Record<keyof CreateUserInput, string>>>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const change = <K extends keyof CreateUserInput>(key: K, value: CreateUserInput[K]) => {
    setForm((current: CreateUserInput) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: undefined }));
  };
  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const nextErrors: Partial<Record<keyof CreateUserInput, string>> = {};
    if (!form.name.trim()) nextErrors.name = "Full name is required.";
    if (!form.email.trim()) nextErrors.email = "Email is required.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) nextErrors.email = "Enter a valid email address.";
    if (!form.password) nextErrors.password = "Temporary password is required.";
    if (!form.role) nextErrors.role = "Role is required.";
    if (!form.cost_centre) nextErrors.cost_centre = "Cost centre is required.";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    setServerError(null);
    setIsSubmitting(true);
    try {
      await submit({ ...form, name: form.name.trim(), email: form.email.trim() });
      close();
    } catch (error) {
      setServerError(error instanceof Error ? error.message : "Unable to create the user.");
    } finally {
      setIsSubmitting(false);
    }
  };
  return <ModalShell onClose={isSubmitting ? () => undefined : close}><ModalHeader title="Add New User" subtitle="Create a user and assign their initial access scope." onClose={close}/><form onSubmit={onSubmit} noValidate><div className="form-body"><div className="field-grid"><Field label="Full Name" error={errors.name}><input value={form.name} onChange={e => change("name", e.target.value)} placeholder="e.g. Rahul Sharma" aria-invalid={Boolean(errors.name)} disabled={isSubmitting}/></Field><Field label="Email" error={errors.email}><input value={form.email} onChange={e => change("email", e.target.value)} type="email" placeholder="name@organization.com" aria-invalid={Boolean(errors.email)} disabled={isSubmitting}/></Field></div><Field label="Temporary Password" error={errors.password}><div className="input-icon"><input value={form.password} onChange={e => change("password", e.target.value)} type="password" placeholder="Enter a secure temporary password" aria-invalid={Boolean(errors.password)} disabled={isSubmitting}/><Icon name="lock" size={16}/></div></Field><div className="field-grid"><Field label="Role" error={errors.role}><select value={form.role} onChange={e => change("role", e.target.value as Role)} disabled={isSubmitting}><option>Employee</option><option>Manager</option><option>Admin</option></select></Field><Field label="Cost Centre" error={errors.cost_centre}><select value={form.cost_centre} onChange={e => change("cost_centre", e.target.value)} disabled={isSubmitting}>{costCentres.slice(1).map(c => <option key={c}>{c}</option>)}</select></Field></div>{serverError && <div className="form-error" role="alert"><Icon name="alert" size={16}/><span>{serverError}</span></div>}<div className="security-copy"><Icon name="lock" size={16}/><span>Passwords are securely hashed by the L.E.D.G.E.R. backend.</span></div></div><div className="modal-actions"><Button variant="secondary" onClick={close} disabled={isSubmitting}>Cancel</Button><Button type="submit" loading={isSubmitting}>{isSubmitting ? "Creating User..." : "Create User"}</Button></div></form></ModalShell>;
}

function EditUserModal({ user, close, requestConfirmation, save }: { user: User; close: () => void; requestConfirmation: (role: Role, cost: string) => void; save: (role: Role, cost: string) => Promise<void> }) {
  const [role, setRole] = useState<Role>(user.role);
  const [cost, setCost] = useState(user.costCentre === "Organization" ? "CC-TECH" : user.costCentre);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const onSave = async () => {
    if (role !== user.role) {
      requestConfirmation(role, cost);
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      await save(role, cost);
      close();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update this user.");
    } finally {
      setIsSubmitting(false);
    }
  };
  return <ModalShell onClose={close}><ModalHeader title="Manage User" subtitle="Review and update this user’s access." onClose={close}/><div className="form-body"><div className="modal-user"><span className="large-avatar">{initials(user.name)}</span><div><b>{user.name}</b><span>{user.email}</span></div><StatusBadge status={user.status}/></div><div className="assignment-grid"><div><span>Current Role</span><RoleBadge role={user.role}/></div><Field label="New Role"><select value={role} onChange={e => setRole(e.target.value as Role)} disabled={isSubmitting}><option>Employee</option><option>Manager</option><option>Admin</option></select></Field><div><span>Current Cost Centre</span><CostCentreBadge value={user.costCentre}/></div><Field label="New Cost Centre"><select value={cost} onChange={e => setCost(e.target.value)} disabled={isSubmitting}>{costCentres.slice(1).map(c => <option key={c}>{c}</option>)}</select></Field></div>{error && <div className="form-error" role="alert"><Icon name="alert" size={16}/><span>{error}</span></div>}<div className="warning-copy"><Icon name="alert" size={17}/><span>Role and access changes affect this user’s authorized financial data.</span></div></div><div className="modal-actions"><Button variant="secondary" onClick={close} disabled={isSubmitting}>Cancel</Button><Button onClick={onSave} loading={isSubmitting}>{isSubmitting ? "Saving..." : "Save Changes"}</Button></div></ModalShell>;
}

function ConfirmRoleChangeModal({ user, role, close, confirm }: { user: User; role: Role; close: () => void; confirm: () => Promise<void> }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const onConfirm = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await confirm();
      close();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update this user.");
    } finally {
      setIsSubmitting(false);
    }
  };
  return <ModalShell onClose={close} size="small"><div className="confirm-body"><div className="confirm-icon"><Icon name="shield" size={22}/></div><h2>Change role?</h2><p>You are changing <b>{user.name}</b> from <RoleBadge role={user.role}/> to <RoleBadge role={role}/>.</p>{error && <div className="form-error" role="alert"><Icon name="alert" size={16}/><span>{error}</span></div>}<div className="warning-copy"><Icon name="alert" size={17}/><span>This changes the financial data they are authorized to access.</span></div></div><div className="modal-actions"><Button variant="secondary" onClick={close} disabled={isSubmitting}>Cancel</Button><Button onClick={onConfirm} loading={isSubmitting}>{isSubmitting ? "Saving..." : "Confirm Change"}</Button></div></ModalShell>;
}

function UserDetailsDrawer({ user, close }: { user: User; close: () => void }) {
  const scope = user.role === "Admin" ? "Organization-wide" : user.role === "Manager" ? user.costCentre : `Employee User ${user.id}`;
  return <div className="modal-layer"><button className="modal-backdrop" onClick={close} aria-label="Close drawer"/><aside className="drawer"><div className="drawer-head"><span>User details</span><button onClick={close} aria-label="Close"><Icon name="close"/></button></div><div className="drawer-profile"><span className="large-avatar">{initials(user.name)}</span><h2>{user.name}</h2><p>{user.email}</p><StatusBadge status={user.status}/></div><div className="details-list">{[["Email", user.email], ["Role", <RoleBadge role={user.role}/>], ["Cost Centre", <CostCentreBadge value={user.costCentre}/>], ["Status", user.status], ["Created", user.created], ["Last active", user.lastActive]].map(([k, v]) => <div key={String(k)}><span>{k}</span><b>{v}</b></div>)}</div><div className="scope-card"><div><Icon name="lock" size={17}/><span>ACCESS SCOPE</span></div><strong>{user.role}</strong><p>{scope}</p></div><div className="drawer-actions"><Button variant="secondary" onClick={close}>Close</Button><Button>Edit User</Button></div></aside></div>;
}

function LoadingState({ variant = "table" }: { variant?: "dashboard" | "table" | "details" | "modal" }) {
  const rows = variant === "dashboard" ? 4 : variant === "table" ? 5 : 3;
  return <div className={`loading-state loading-${variant}`} role="status" aria-label="Loading"><span className="skeleton skeleton-title"/>{Array.from({ length: rows }).map((_, index) => <span className="skeleton skeleton-row" key={index}/>)}</div>;
}

function ErrorState({ type }: { type: "error" | "unauthorized" }) {
  const unauthorized = type === "unauthorized";
  return <div className="standalone-state"><div className={`state-icon ${unauthorized ? "danger" : ""}`}><Icon name={unauthorized ? "lock" : "refresh"} size={22}/></div><h3>{unauthorized ? "Unauthorized" : "Failed to load users"}</h3><p>{unauthorized ? "You do not have permission to access the Admin Portal." : "Unable to retrieve users from the secure backend."}</p><Button variant="secondary" icon={unauthorized ? "arrow" : "refresh"}>{unauthorized ? "Return to Dashboard" : "Try again"}</Button></div>;
}

function AuditLogView({ logs, isLoading, error, page, totalPages, previewMode, refresh, changePage, select }: { logs: AuditLog[]; isLoading: boolean; error: string | null; page: number; totalPages?: number; previewMode: boolean; refresh: () => void; changePage: (page: number) => void; select: (log: AuditLog) => void }) {
  return <><PageTitle title="Audit Log" subtitle="Review secure organization and access activity." action={<Button variant="secondary" icon="refresh" onClick={refresh} loading={isLoading}>Refresh</Button>}/>
    <section className="panel users-panel">
      {previewMode && <div className="preview-notice">Design preview data · Connect VITE_API_BASE_URL for live audit records</div>}
      {isLoading ? <div className="table-state"><LoadingState variant="table"/><span>Loading audit logs...</span></div> : error ? <div className="empty-state"><div className="state-icon danger"><Icon name="refresh"/></div><h3>Unable to load audit logs</h3><p>{error}</p><Button variant="secondary" icon="refresh" onClick={refresh}>Try again</Button></div> : logs.length ? <><div className="table-scroll"><table className="user-table audit-table"><thead><tr><th>Audit ID</th><th>Timestamp</th><th>User</th><th>Action</th><th>Resource</th><th>Status</th><th>Role</th><th>Cost Centre</th></tr></thead><tbody>{logs.map(log => <tr key={log.auditId} onClick={() => select(log)}><td><button className="audit-link">{log.auditId}</button></td><td>{log.timestamp}</td><td>{log.user}</td><td><span className="audit-action">{log.action.replace(/_/g, " ")}</span></td><td>{log.resource}</td><td><StatusBadge status={log.status === "Success" ? "Active" : "Inactive"}/></td><td>{log.role ? <RoleBadge role={log.role}/> : "—"}</td><td>{log.costCentre ? <CostCentreBadge value={log.costCentre}/> : "—"}</td></tr>)}</tbody></table></div><div className="table-foot"><span>Page <b>{page}</b>{totalPages ? <> of <b>{totalPages}</b></> : null}</span><div><button disabled={page <= 1} onClick={() => changePage(page - 1)}>Previous</button><button className="page-active">{page}</button><button disabled={!totalPages || page >= totalPages} onClick={() => changePage(page + 1)}>Next</button></div></div></> : <div className="empty-state"><div className="state-icon"><Icon name="audit"/></div><h3>No audit records found</h3><p>There is no organization activity to display.</p><Button variant="secondary" icon="refresh" onClick={refresh}>Refresh</Button></div>}
    </section>
  </>;
}

function sanitizeAuditValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sanitizeAuditValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value as Record<string, unknown>)
      .filter(([key]) => !/(password|secret|token|cookie|api.?key)/i.test(key))
      .map(([key, nestedValue]) => [key, sanitizeAuditValue(nestedValue)]));
  }
  return value;
}

function AuditDetailsModal({ log, loading, error, close }: { log: AuditLog; loading: boolean; error: string | null; close: () => void }) {
  const safeDetails = Object.entries(sanitizeAuditValue(log.details || {}) as Record<string, unknown>);
  return <ModalShell onClose={close}><ModalHeader title="Audit Details" subtitle={`Audit reference ${log.auditId}`} onClose={close}/>{loading ? <div className="form-body"><LoadingState variant="details"/></div> : error ? <div className="form-body"><div className="form-error" role="alert"><Icon name="alert" size={16}/><span>{error}</span></div></div> : <div className="form-body"><div className="audit-details">{[["Audit ID", log.auditId], ["Timestamp", log.timestamp], ["User", log.user], ["Action", log.action.replace(/_/g, " ")], ["Resource", log.resource], ["Status", log.status], ["Role", log.role || "—"], ["Cost Centre", log.costCentre || "—"], ...safeDetails.map(([key, value]) => [key.replace(/_/g, " "), typeof value === "object" ? JSON.stringify(value) : String(value)])].map(([label, value]) => <div key={String(label)}><span>{label}</span><b>{value}</b></div>)}</div><div className="security-copy"><Icon name="lock" size={16}/><span>Sensitive authentication and credential fields are never displayed.</span></div></div>}<div className="modal-actions"><Button variant="secondary" onClick={close}>Close</Button></div></ModalShell>;
}

function Toast({ message, dismiss }: { message: string; dismiss: () => void }) {
  useEffect(() => {
    const timeout = window.setTimeout(dismiss, 4500);
    return () => window.clearTimeout(timeout);
  }, [dismiss]);
  return <div className="toast" role="status"><span className="toast-icon"><Icon name="check" size={15}/></span><span>{message}</span><button onClick={dismiss} aria-label="Dismiss notification"><Icon name="close" size={14}/></button></div>;
}

function AdminSection() {
  return <><PageTitle title="Admin" subtitle="Security and organization access status."/><div className="admin-grid"><section className="panel security-panel"><div className="section-head"><div><h2>Access security</h2><p>Organization-wide controls</p></div><span className="status active"><i></i>Protected</span></div><div className="security-row"><span className="stat-icon"><Icon name="shield"/></span><div><b>Role-based access control</b><p>Admin-only access is active for this portal.</p></div><Icon name="check"/></div><div className="security-row"><span className="stat-icon"><Icon name="lock"/></span><div><b>Secure credential storage</b><p>Passwords are hashed by the backend.</p></div><Icon name="check"/></div></section><section className="panel"><div className="section-head"><div><h2>System states</h2><p>Reusable permission and error patterns</p></div></div><div className="state-gallery"><ErrorState type="unauthorized"/><ErrorState type="error"/></div></section></div></>;
}

function initials(name: string) { return name.split(" ").map(n => n[0]).slice(0, 2).join(""); }

export default function AdminPortal({ authenticatedUser }: { authenticatedUser?: AuthenticatedUser | null } = {}) {
  const apiConfigured = isAdminApiConfigured();
  const isUiAuthorized = !authenticatedUser || authenticatedUser.role === "Admin";
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    const saved = localStorage.getItem("ledger-admin-theme");
    if (saved === "dark" || saved === "light") return saved;
    const rootTheme = document.documentElement.dataset.theme;
    if (rootTheme === "dark" || rootTheme === "light") return rootTheme;
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  });
  const [page, setPage] = useState<Page>("dashboard");
  const [navOpen, setNavOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [details, setDetails] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>(apiConfigured ? [] : mockUsers);
  const [isLoadingUsers, setIsLoadingUsers] = useState(apiConfigured);
  const [usersError, setUsersError] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<{ user: User; role: Role; cost: string } | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>(apiConfigured ? [] : mockAuditLogs);
  const [auditPage, setAuditPage] = useState(1);
  const [auditTotalPages, setAuditTotalPages] = useState<number | undefined>();
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [selectedAudit, setSelectedAudit] = useState<AuditLog | null>(null);
  const [auditDetailsLoading, setAuditDetailsLoading] = useState(false);
  const [auditDetailsError, setAuditDetailsError] = useState<string | null>(null);

  const loadUsers = useCallback(async () => {
    if (!apiConfigured || !isUiAuthorized) return;
    setIsLoadingUsers(true);
    setUsersError(null);
    try {
      setUsers(await getUsers());
    } catch (error) {
      setUsers([]);
      setUsersError(error instanceof Error ? error.message : "Unable to load users.");
    } finally {
      setIsLoadingUsers(false);
    }
  }, [apiConfigured, isUiAuthorized]);

  const loadAuditLogs = useCallback(async (requestedPage = 1) => {
    if (!apiConfigured || !isUiAuthorized) return;
    setAuditLoading(true);
    setAuditError(null);
    try {
      const response = await getAuditLogs(requestedPage);
      setAuditLogs(response.items);
      setAuditPage(response.page || requestedPage);
      setAuditTotalPages(response.totalPages);
    } catch (error) {
      setAuditLogs([]);
      setAuditError(error instanceof Error ? error.message : "Unable to load audit logs.");
    } finally {
      setAuditLoading(false);
    }
  }, [apiConfigured, isUiAuthorized]);

  useEffect(() => {
    localStorage.setItem("ledger-admin-theme", theme);
  }, [theme]);
  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);
  useEffect(() => {
    if (page === "audit") void loadAuditLogs(auditPage);
  }, [page, loadAuditLogs]);

  const submitNewUser = async (data: CreateUserInput) => {
    await createUser(data);
    await loadUsers();
    setToast("User created successfully.");
  };
  const saveUser = async (user: User, role: Role, cost: string) => {
    const payload: UpdateUserInput = { role, cost_centre: cost };
    await updateUser(user.id, payload);
    await loadUsers();
    setToast("User access updated successfully.");
  };
  const selectAudit = async (log: AuditLog) => {
    setSelectedAudit(log);
    setAuditDetailsError(null);
    if (!apiConfigured) return;
    setAuditDetailsLoading(true);
    try {
      setSelectedAudit(await getAuditLog(log.auditId));
    } catch (error) {
      setAuditDetailsError(error instanceof Error ? error.message : "Unable to load audit details.");
    } finally {
      setAuditDetailsLoading(false);
    }
  };
  const requestConfirm = (role: Role, cost: string) => { if (editing) { setConfirmation({ user: editing, role, cost }); setEditing(null); } };
  if (!isUiAuthorized) return <div className="access-denied-page"><Logo/><ErrorState type="unauthorized"/></div>;
  return <div className="admin-portal" data-theme={theme}><AdminSidebar page={page} setPage={setPage} open={navOpen} close={() => setNavOpen(false)}/><div className="app-main"><AdminHeader toggleNav={() => setNavOpen(true)} theme={theme} toggleTheme={() => setTheme(current => current === "dark" ? "light" : "dark")} user={authenticatedUser}/><main>{page === "dashboard" && <Dashboard openAudit={() => setPage("audit")}/>} {page === "users" && <UserManagement users={users} isLoading={isLoadingUsers} error={usersError} refresh={() => void loadUsers()} previewMode={!apiConfigured} openAdd={() => setAddOpen(true)} openEdit={setEditing} openDetails={setDetails}/>} {page === "audit" && <AuditLogView logs={auditLogs} isLoading={auditLoading} error={auditError} page={auditPage} totalPages={auditTotalPages} previewMode={!apiConfigured} refresh={() => void loadAuditLogs(auditPage)} changePage={nextPage => void loadAuditLogs(nextPage)} select={log => void selectAudit(log)}/>} {page === "admin" && <AdminSection/>}</main><footer><span>L.E.D.G.E.R. · Language-Enabled Data Governance &amp; Expense Resolution</span><span>Secure session · v1.0</span></footer></div>
    {addOpen && <AddUserModal close={() => setAddOpen(false)} submit={submitNewUser}/>}
    {editing && <EditUserModal user={editing} close={() => setEditing(null)} requestConfirmation={requestConfirm} save={(role, cost) => saveUser(editing, role, cost)}/>}
    {details && <UserDetailsDrawer user={details} close={() => setDetails(null)}/>}
    {confirmation && <ConfirmRoleChangeModal user={confirmation.user} role={confirmation.role} close={() => setConfirmation(null)} confirm={() => saveUser(confirmation.user, confirmation.role, confirmation.cost)}/>}
    {selectedAudit && <AuditDetailsModal log={selectedAudit} loading={auditDetailsLoading} error={auditDetailsError} close={() => setSelectedAudit(null)}/>}
    {toast && <Toast message={toast} dismiss={() => setToast(null)}/>}
  </div>;
}
