# Auth/RBAC integration contract

The `auth` package owns credential verification, trusted user identity,
request/task-local session state, role checks, and cost-centre authorization.

## Authenticate and establish context

```python
from auth import authenticate_user, set_authenticated_user

user = authenticate_user(email, password)
if user is not None:
    set_authenticated_user(user)
```

`authenticate_user` returns `AuthenticatedUser` or `None`. The safe identity
contains `user_id`, `name`, `email`, `role`, and `cost_centre`; it never
contains the stored password hash. Credentials and hashes are not logged.

## Consume trusted context

```python
from auth import get_current_user, get_authorized_scope

user = get_current_user()
if user is None:
    raise PermissionError("Authentication is required")
authorization = get_authorized_scope(user)
# {"user_id": ..., "role": ..., "cost_centre": ...}
```

Downstream code should use `authorization["cost_centre"]` for data scope.
Optional request role or cost-centre values passed to `get_authorized_scope`
are checked against the authenticated identity and a conflicting value is
denied. Request values never replace trusted identity fields.

`has_permission` and `require_permission` check centralized role grants.
No business permission matrix is defined yet, so every permission is denied
until an explicit grant is approved and added to `ROLE_PERMISSIONS`.

## Session lifecycle

Use `set_authenticated_user`, `get_current_user`, `is_authenticated`, and
`logout` from the package. The current implementation stores only a trusted
identity in a Python `ContextVar`; it is scoped to the current execution
context, not a persistent browser session. The hosting request layer must
establish and clear context for each request and must not trust a serialized
client-supplied identity.
