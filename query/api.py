"""FastAPI boundary for the deterministic Query Compiler.

The request body contains only query intent data. Authorization scope is
resolved by the trusted Auth/RBAC dependency and is never accepted from the
frontend as a trusted value.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from .compiler import compile_query
from .schema import AuthorizationScope, CompilerResponse

router = APIRouter(prefix="/query", tags=["Query Compiler"])


class CompileQueryRequest(BaseModel):
    """Client input. Authorization fields are deliberately not accepted."""

    model_config = ConfigDict(extra="forbid")

    prompt: str
    current_date: Optional[date] = None


def get_trusted_scope() -> AuthorizationScope:
    """Resolve scope from the host application's Auth/RBAC session.

    This adapter does not authenticate or authorize anything. It only
    consumes the trusted Auth/RBAC result and converts it to the compiler's
    schema. The auth package is imported here so the Query Compiler remains
    independently testable until the host app merges Auth/RBAC.
    """

    try:
        from auth import AuthorizationError, get_authorized_scope, get_current_user
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Auth/RBAC integration is not available yet.",
        ) from exc

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
