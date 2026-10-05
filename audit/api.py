"""FastAPI router for audit record retrieval."""

from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from audit.logger import DEFAULT_DB, get_audit_record, get_recent
from auth.rbac import AuthorizationError, get_authorized_scope, has_permission
from auth.session import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])


def require_audit_view_permission():
    """Verify the current session user has audit:view permission."""
    user = get_current_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not has_permission(user, "audit:view"):
        raise HTTPException(
            status_code=403, detail="You do not have permission to view audit logs."
        )
    return user


@router.get("/recent")
def get_recent_audits(
    limit: int = Query(default=20, ge=1, le=100),
    user=Depends(require_audit_view_permission),
) -> List[dict[str, Any]]:
    """Retrieve the most recent audit records."""
    records = get_recent(limit=limit)
    return records


@router.get("/{query_id}")
def get_audit_by_id(
    query_id: str,
    user=Depends(require_audit_view_permission),
) -> dict[str, Any]:
    """Retrieve an audit record by its unique query_id."""
    record = get_audit_record(query_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Audit record '{query_id}' not found.")
    return record
