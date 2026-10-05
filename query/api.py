"""FastAPI boundary for the deterministic Query Compiler.

The request body contains only query intent data. Authorization scope is
resolved by the trusted Auth/RBAC dependency and is never accepted from the
frontend as a trusted value.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict

from .compiler import compile_query
from .schema import AuthorizationScope, CompilerResponse, ScopeType

router = APIRouter(prefix="/query", tags=["Query Compiler"])


class CompileQueryRequest(BaseModel):
    """Client input. Authorization fields are deliberately not accepted."""

    model_config = ConfigDict(extra="forbid")

    prompt: str
    current_date: Optional[date] = None


DEMO_USERS: dict[str, AuthorizationScope] = {
    "U-001": AuthorizationScope(
        user_id="U-001",
        role="Employee",
        scope_type=ScopeType.user,
        scope_user_id="U-001",
    ),
    "U-002": AuthorizationScope(
        user_id="U-002",
        role="Manager",
        scope_type=ScopeType.cost_centre,
        cost_centre="CC-TECH",
    ),
    "U-003": AuthorizationScope(
        user_id="U-003",
        role="Admin",
        scope_type=ScopeType.organization,
    ),
}


def get_trusted_scope(
    x_demo_user: str = Header(default="U-002", alias="X-Demo-User"),
) -> AuthorizationScope:
    """Resolve trusted scope without accepting authorization in the body.

    In production the host application's Auth/RBAC dependency should provide
    the scope. Until that module is integrated, the hackathon sandbox uses
    the X-Demo-User header to select one of three fixed server-side personas.
    The header selects a pre-defined scope; it cannot provide arbitrary role,
    cost centre, organization, or user-scope values.
    """
    try:
        from auth import AuthorizationError, get_authorized_scope, get_current_user
    except (ImportError, AttributeError):
        scope = DEMO_USERS.get(x_demo_user)
        if scope is None:
            raise HTTPException(
                status_code=401,
                detail="Unknown or missing demo user",
            )
        return scope

    user = get_current_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        trusted = get_authorized_scope(user)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail="Authorization denied.") from exc

    return AuthorizationScope.model_validate(trusted)

@router.post("/compile", response_model=CompilerResponse)
def compile_query_endpoint(
    request: CompileQueryRequest,
    scope: AuthorizationScope = Depends(get_trusted_scope),
) -> CompilerResponse:
    """Compile a natural-language financial question using trusted scope."""

    return compile_query(
        prompt=request.prompt,
        scope=scope,
        current_date=request.current_date,
    )


@router.get("/health")
def health_check():
    """Simple liveness check for the Query Compiler router."""

    return {"status": "ok", "module": "query-compiler"}
