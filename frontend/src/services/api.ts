const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export type LedgerUser = { user_id: string; name: string; email: string; role: string; cost_centre: string };
export type QueryResult = { status: string; result: unknown; currency: string | null; source_rows: string[]; query_id?: number | string; formula?: string; row_count?: number; message?: string; error?: string; filters?: Record<string, unknown>; parsed_query?: Record<string, unknown> };
export type AnalyticsOverview = { scope: { scope_type: string; scope_value: string }; period: { start: string; end: string }; expense_count: number; spend_by_currency: { currency: string; amount: number; count: number }[]; monthly_spending: { month: string; currency: string; amount: number; count: number }[]; category_spending: { category: string; currency: string; amount: number; count: number }[]; cost_centre_spending: { cost_centre: string; currency: string; amount: number; count: number }[]; budget_comparison: { available: boolean; reason?: string } };
export type AdminOptions = { roles: string[]; cost_centres: string[] };
export type AdminUser = { user_id: string; name: string; email: string; role: string; cost_centre: string };
export type AdminSummary = { user_count: number; users_by_role: { role: string; count: number }[]; expense_count: number; spend_by_currency: { currency: string; amount: number }[]; cost_centres: string[] };
export type ExpenseInput = { category: string; amount: number; currency: string; date: string; description?: string };

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}${path}`, { ...init, credentials: "include", headers: { "Content-Type": "application/json", ...init.headers } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || body.error || `Request failed (${response.status}).`);
  return body as T;
}

export const login = (email: string, password: string) => request<LedgerUser>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
export const currentUser = () => request<LedgerUser>("/auth/me");
export const logout = () => request<{ status: string }>("/auth/logout", { method: "POST" });
export const executeQuery = (prompt: string) => request<QueryResult>("/query/execute", { method: "POST", body: JSON.stringify({ prompt }) });
export const googleStatus = () => request<{ enabled: boolean }>("/auth/google/status");
export const startGoogleLogin = () => { window.location.assign(`${API}/auth/google/login`); };
export const getAnalyticsOverview = () => request<AnalyticsOverview>("/analytics/overview");
export const getAdminSummary = () => request<AdminSummary>("/admin/summary");
export const getAdminOptions = () => request<AdminOptions>("/admin/options");
export const getAdminUsers = (filters: { search?: string; role?: string; cost_centre?: string } = {}) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) params.set(key, value); });
  return request<AdminUser[]>(`/admin/users${params.size ? `?${params}` : ""}`);
};
export const createAdminUser = (body: { name: string; email: string; password: string; role: string; cost_centre: string }) => request<AdminUser>("/admin/users", { method: "POST", body: JSON.stringify(body) });
export const updateAdminRole = (id: string, role: string) => request<AdminUser>(`/admin/users/${encodeURIComponent(id)}/role`, { method: "PATCH", body: JSON.stringify({ role }) });
export const updateAdminCostCentre = (id: string, cost_centre: string) => request<AdminUser>(`/admin/users/${encodeURIComponent(id)}/cost-centre`, { method: "PATCH", body: JSON.stringify({ cost_centre }) });
export const createExpense = (body: ExpenseInput) => request<{ expense_id: string; user_id: string; cost_centre: string; category: string; amount: number; currency: string; date: string; description: string }>("/expenses", { method: "POST", body: JSON.stringify(body) });
