"""
api.py — FastAPI router for the Query Compiler module (Niketan)

Exposes compile_query() as an HTTP endpoint so other services (or a
separate frontend) can call it. This is a ROUTER, not a standalone app —
it's meant to be plugged into the team's shared FastAPI app alongside
everyone else's modules (Auth, Database, Calculation Engine, etc).

Usage from the team's main app.py:
    from fastapi import FastAPI
    from query.api import router as query_router

    app = FastAPI(title="LEDGER API")
    app.include_router(query_router)

Then the endpoint is available at: POST /query/compile
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .compiler import compile_query
from .schema import CompilerResponse

router = APIRouter(prefix="/query", tags=["Query Compiler"])


class CompileQueryRequest(BaseModel):
    """What the frontend/client sends in the request body."""
    prompt: str
    user_scope: str
    # NOTE (security): user_scope should eventually be derived server-side
    # from an authenticated session/token (Shubham's Auth module), not
    # trusted directly from the request body — see the project's own
    # "frontend must not be trusted to define authorized cost centre" rule.
    # Accepting it here is a placeholder until Auth exposes a dependency
    # (e.g. Depends(get_current_user_scope)) that this endpoint can use
    # instead of this field.
    current_date: Optional[date] = None


@router.post("/compile", response_model=CompilerResponse)
def compile_query_endpoint(request: CompileQueryRequest) -> CompilerResponse:
    """
    Converts a natural-language financial question into a validated
    structured query, or a CLARIFY / REFUSED response.
    """
    return compile_query(
        prompt=request.prompt,
        user_scope=request.user_scope,
        current_date=request.current_date,
    )


@router.get("/health")
def health_check():
    """Simple check that this router is alive — useful for teammates
    wiring the frontend to confirm the endpoint is reachable."""
    return {"status": "ok", "module": "query-compiler"}
