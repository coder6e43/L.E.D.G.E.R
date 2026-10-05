# Auth/RBAC integration contract

The `auth` package owns bcrypt credential verification, trusted identity,
request/task-local session context, role permissions, and data-scope
authorization. It does not create users, change roles, modify cost-centre
assignments, or insert expenses; it exposes authorization decisions for those
future operations.

## Authenticate and establish context

```python
from auth import authenticate_user, set_authenticated_user

user = authenticate_user(email, password)
if user is not None:
    set_authenticated_user(user)
```

Authentication returns a frozen `AuthenticatedUser` or `None`. Its public
fields are `user_id`, `name`, `email`, `role`, and the user's assigned
`cost_centre`. It never contains a password or password hash. Credential
failures do not reveal whether an account exists; credentials and hashes are
not logged.

## Session lifecycle

Use `set_authenticated_user`, `get_current_user`, `is_authenticated`, and
`logout` from the package. The session accepts only a trusted
`AuthenticatedUser`. The current implementation stores the identity in a
Python `ContextVar`, scoped to an execution context; it is not a persistent
browser session. The host request layer must establish and clear context for
each request and must not trust a client-serialized identity.

## Permission matrix

Permissions are centralized in `ROLE_PERMISSIONS`; `has_permission` returns
false for undefined permissions and `require_permission` raises
`AuthorizationError`.

| Permission | Employee | Manager | Admin |
| --- | --- | --- | --- |
| `query:ask` | Yes | Yes | Yes |
| `expense:view_own` | Yes | Yes | Yes |
| `expense:create_own` | Yes | Yes | Yes |
| `expense:view_cost_centre` | No | Yes | Yes |
| `budget:view_cost_centre` | No | Yes | Yes |
| `trend:view_cost_centre` | No | Yes | Yes |
| `audit:view` | No | No | Yes |
| `report:export` | No | No | Yes |
| `cost_centre:view_all` | No | No | Yes |
| `user:manage` | No | No | Yes |
| `role:assign` | No | No | Yes |
| `cost_centre:manage_access` | No | No | Yes |

## Data scope

Call `get_current_user()` and then `get_authorized_scope(user)`. The returned
mapping has a role-derived `scope_type` and canonical `scope_value`:

- Employee: `scope_type="user"`, `scope_value` is the authenticated user's ID,
  and `scope_user_id` preserves compatibility with typed downstream adapters.
  Employee scope does not include a cost-centre-wide grant.
- Manager: `scope_type="cost_centre"`, `scope_value` is the authenticated
  user's assigned centre, and `cost_centre` preserves compatibility with
  typed downstream adapters.
- Admin: `scope_type="organization"` and `scope_value="organization"`; no
  single cost-centre filter is represented as the complete scope.

Never use request-provided `user_id`, `role`, `cost_centre`, or `scope_value`
as trusted identity or authorization scope. Conflicting role or scope values
are rejected. `authorize_cost_centre` lets a Manager operate only in their
assigned centre; an Admin may authorize a specific centre filter because the
Admin has organization-wide access. Employees cannot use it to widen their
own-data scope.

## Role management and future expense authorization

`authorize_role_assignment(actor, new_role, target_user_id)` authorizes role
assignment or change for an Admin and accepts only `Employee`, `Manager`, or
`Admin`. It does not perform user creation or database updates.
`authorize_cost_centre_access_management(actor, target_user_id, cost_centre)`
provides the Admin-only authorization decision for future access management.
Neither helper mutates user data.

`authorize_expense_creation(user, requested_user_id, requested_cost_centre)`
authorizes only `expense:create_own` and returns the authenticated user's
trusted ID and assigned centre. It does not insert an expense. On-behalf-of
expense creation is not granted by the current policy.

## Current execution boundary

The calculation engine currently accepts only one `authorized_cost_centre`.
The app integration therefore executes cost-centre-scope queries only and
fails closed for Employee user scope and Admin organization scope until the
calculation interface can represent those scopes. This limitation does not
change the permissions above; downstream modules must consume
`scope_type` explicitly and must not convert user or organization scope into
an arbitrary cost-centre value.
