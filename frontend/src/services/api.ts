const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type LedgerUser = { user_id: string; name: string; email: string; role: string; cost_centre: string };
export type QueryResult = { status: string; result: unknown; currency: string | null; source_rows: string[]; query_id?: number | string; formula?: string; row_count?: number; message?: string; error?: string };

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
