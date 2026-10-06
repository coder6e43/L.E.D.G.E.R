import type { AdminUser, AuditLog } from "../types/admin";

// Explicit design-preview data. API requests never fall back to these records.
export const mockUsers: AdminUser[] = [
  { id: "U003", name: "Akanksha Bhardwaj", email: "akanksha@example.com", role: "Employee", costCentre: "CC-MARKETING", status: "Active", created: "12 Jan 2025", lastActive: "Today, 09:42" },
  { id: "U018", name: "Shaurya Mehta", email: "shaurya@example.com", role: "Manager", costCentre: "CC-TECH", status: "Active", created: "08 Jan 2025", lastActive: "Today, 08:16" },
  { id: "U024", name: "Divyapunj Rao", email: "divyapunj@example.com", role: "Admin", costCentre: "Organization", status: "Active", created: "18 Dec 2024", lastActive: "Yesterday, 17:40" },
  { id: "U041", name: "Rahul Sharma", email: "rahul@example.com", role: "Employee", costCentre: "CC-FINANCE", status: "Active", created: "02 Feb 2025", lastActive: "Yesterday, 15:22" },
  { id: "U052", name: "Priya Singh", email: "priya@example.com", role: "Manager", costCentre: "CC-HR", status: "Invited", created: "19 Feb 2025", lastActive: "Invitation pending" },
];

export const mockAuditLogs: AuditLog[] = [
  { auditId: "AUD-1048", timestamp: "Today, 09:42", user: "Rahul Sharma", action: "ROLE_CHANGED", resource: "User U041", status: "Success", role: "Manager", costCentre: "CC-FINANCE" },
  { auditId: "AUD-1047", timestamp: "Today, 09:29", user: "Priya Singh", action: "USER_CREATED", resource: "User U052", status: "Success", role: "Manager", costCentre: "CC-HR" },
  { auditId: "AUD-1046", timestamp: "Today, 08:16", user: "Shaurya Mehta", action: "LOGIN_SUCCESS", resource: "Admin Portal", status: "Success", role: "Manager", costCentre: "CC-TECH" },
];
