export type AdminRole = "Employee" | "Manager" | "Admin";

export interface AdminUser {
  user_id: string;
  name: string;
  email: string;
  role: string;
  cost_centre: string;
  status?: string;
  created?: string;
}

export interface AdminSummary {
  user_count: number;
  users_by_role: Array<{ role: string; count: number }>;
  expense_count: number;
  spend_by_currency: Array<{ currency: string; amount: number }>;
}

export interface AdminOptions {
  roles: string[];
  cost_centres: string[];
}

export interface CreateUserInput {
  name: string;
  email: string;
  password: string;
  role: string;
  cost_centre: string;
}

export interface AuditLogItem {
  audit_id: string;
  query_id: string;
  timestamp: string;
  user_id: string;
  role: string;
  cost_centre: string;
  natural_query: string;
  intent: string;
  category?: string;
  execution_time_ms?: number;
  source_row_count?: number;
  calculation_result?: number;
  currency?: string;
  authorized_expense_ids?: string[];
}

export interface SystemMetrics {
  databaseStatus: "Connected" | "Degraded" | "Disconnected";
  databasePath: string;
  activeSessions: number;
  rbacStatus: "Enforced" | "Disabled";
  auditLogging: "Active" | "Inactive";
}
