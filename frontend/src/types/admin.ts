export type AdminRole = "Employee" | "Manager" | "Admin";

export type UserStatus = "Active" | "Inactive" | "Invited";

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: AdminRole;
  costCentre: string;
  status: UserStatus;
  created: string;
  lastActive: string;
}

export interface CreateUserInput {
  name: string;
  email: string;
  password: string;
  role: AdminRole;
  cost_centre: string;
}

export interface UpdateUserInput {
  role: AdminRole;
  cost_centre: string;
}

export type AuditAction =
  | "USER_CREATED"
  | "ROLE_CHANGED"
  | "COST_CENTRE_CHANGED"
  | "LOGIN_SUCCESS"
  | "LOGIN_FAILED"
  | "LOGOUT"
  | "QUERY_EXECUTED"
  | string;

export interface AuditLog {
  auditId: string;
  timestamp: string;
  user: string;
  action: AuditAction;
  resource: string;
  status: string;
  role?: AdminRole;
  costCentre?: string;
  details?: Record<string, unknown>;
}

export interface AuditLogPage {
  items: AuditLog[];
  page?: number;
  totalPages?: number;
  total?: number;
}

export interface AuthenticatedUser {
  user_id: string;
  name: string;
  email: string;
  role: AdminRole;
  cost_centre: string;
}
