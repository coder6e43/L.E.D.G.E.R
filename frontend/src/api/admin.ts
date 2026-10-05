import type {
  AdminRole,
  AdminUser,
  AuditLog,
  AuditLogPage,
  CreateUserInput,
  UpdateUserInput,
  UserStatus,
} from "../types/admin";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL as string | undefined
)?.replace(/\/+$/, "");

export class AdminApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "AdminApiError";
  }
}

export function isAdminApiConfigured(): boolean {
  return Boolean(API_BASE_URL);
}

function errorMessage(status: number, backendMessage?: string): string {
  if (status === 401) {
    return "Your session has expired. Please sign in again.";
  }

  if (status === 403) {
    return "You do not have permission to perform this action.";
  }

  if (status === 409) {
    return "A user with this email already exists.";
  }

  if (status === 422) {
    return (
      backendMessage ||
      "Please review the submitted information."
    );
  }

  if (status >= 500) {
    return "The L.E.D.G.E.R. backend could not complete the request.";
  }

  return backendMessage || "The request could not be completed.";
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  if (!API_BASE_URL) {
    throw new AdminApiError(
      "Backend connection is not configured.",
    );
  }

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        Accept: "application/json",
        ...(init?.body
          ? { "Content-Type": "application/json" }
          : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new AdminApiError(
      "Unable to connect to the L.E.D.G.E.R. backend.",
    );
  }

  if (!response.ok) {
    let backendMessage: string | undefined;

    try {
      const body = (await response.json()) as {
        detail?: string;
        message?: string;
      };

      backendMessage =
        typeof body.detail === "string"
          ? body.detail
          : body.message;
    } catch {
      // Ignore non-JSON response.
    }

    throw new AdminApiError(
      errorMessage(response.status, backendMessage),
      response.status,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

type ApiUser = {
  user_id: string;
  name: string;
  email: string;
  role: AdminRole;
  cost_centre: string;
  status: UserStatus;
  created?: string;
  created_at?: string;
  last_active?: string;
};

function mapUser(user: ApiUser): AdminUser {
  return {
    id: user.user_id,
    name: user.name,
    email: user.email,
    role: user.role,
    costCentre: user.cost_centre,
    status: user.status,
    created: user.created_at || user.created || "—",
    lastActive: user.last_active || "—",
  };
}

type ApiAuditLog = {
  audit_id: string;
  timestamp: string;
  user?: string;
  user_name?: string;
  action: string;
  resource: string;
  status: string;
  role?: AdminRole;
  cost_centre?: string;
  details?: Record<string, unknown>;
};

function mapAuditLog(log: ApiAuditLog): AuditLog {
  return {
    auditId: log.audit_id,
    timestamp: log.timestamp,
    user: log.user_name || log.user || "System",
    action: log.action,
    resource: log.resource,
    status: log.status,
    role: log.role,
    costCentre: log.cost_centre,
    details: log.details,
  };
}

export async function getUsers(): Promise<AdminUser[]> {
  const response = await request<
    ApiUser[] | { users: ApiUser[] }
  >("/admin/users");

  const users = Array.isArray(response)
    ? response
    : response.users;

  return users.map(mapUser);
}

export async function createUser(
  data: CreateUserInput,
): Promise<AdminUser | void> {
  const response = await request<ApiUser | undefined>(
    "/admin/users",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );

  return response ? mapUser(response) : undefined;
}

export async function updateUser(
  userId: string,
  data: UpdateUserInput,
): Promise<AdminUser | void> {
  const response = await request<ApiUser | undefined>(
    `/admin/users/${encodeURIComponent(userId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    },
  );

  return response ? mapUser(response) : undefined;
}

export async function getAuditLogs(
  page?: number,
): Promise<AuditLogPage> {
  const query = page
    ? `?page=${encodeURIComponent(page)}`
    : "";

  const response = await request<
    | ApiAuditLog[]
    | {
        items?: ApiAuditLog[];
        audit_logs?: ApiAuditLog[];
        page?: number;
        total_pages?: number;
        total?: number;
      }
  >(`/admin/audit-logs${query}`);

  if (Array.isArray(response)) {
    return {
      items: response.map(mapAuditLog),
    };
  }

  return {
    items: (
      response.items ||
      response.audit_logs ||
      []
    ).map(mapAuditLog),
    page: response.page,
    totalPages: response.total_pages,
    total: response.total,
  };
}

export async function getAuditLog(
  auditId: string,
): Promise<AuditLog> {
  const response = await request<ApiAuditLog>(
    `/admin/audit-logs/${encodeURIComponent(auditId)}`,
  );

  return mapAuditLog(response);
}