"""Google OpenID Connect handoff that mints the normal LEDGER session.

Google identities must match a pre-provisioned local account. This flow does
not create a parallel identity store or assign a role from provider data.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException, Request as FastAPIRequest
from fastapi.responses import RedirectResponse

from auth.authentication import AuthenticatedUser, VALID_ROLES
from database.connection import get_connection

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def google_oauth_configured() -> bool:
    return all(
        os.environ.get(key, "").strip()
        for key in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI")
    )


def google_login_redirect(request: FastAPIRequest) -> RedirectResponse:
    if not google_oauth_configured():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    state = secrets.token_urlsafe(32)
    request.session["google_oauth_state"] = state
    request.session["google_oauth_started"] = int(time.time())
    params = {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}", status_code=302)


def google_callback(request: FastAPIRequest, code: str, state: str) -> RedirectResponse:
    if not google_oauth_configured():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    expected_state = request.session.pop("google_oauth_state", None)
    started = request.session.pop("google_oauth_started", 0)
    if (
        not isinstance(expected_state, str)
        or not secrets.compare_digest(expected_state, state)
        or not isinstance(started, int)
        or time.time() - started > 600
    ):
        request.session.clear()
        raise HTTPException(status_code=400, detail="Google sign-in could not be verified.")
    if not code or len(code) > 4096:
        request.session.clear()
        raise HTTPException(status_code=400, detail="Google sign-in could not be verified.")

    try:
        token_payload = _post_form(
            GOOGLE_TOKEN_URL,
            {
                "code": code,
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
                "grant_type": "authorization_code",
            },
        )
        access_token = token_payload.get("access_token")
        token_type = token_payload.get("token_type", "Bearer")
        if not isinstance(access_token, str) or not isinstance(token_type, str) or token_type.lower() != "bearer":
            raise ValueError("Invalid provider token response")
        profile = _get_json(
            GOOGLE_USERINFO_URL,
            {"Authorization": f"Bearer {access_token}"},
        )
        email = profile.get("email")
        subject = profile.get("sub")
        if profile.get("email_verified") is not True or not isinstance(email, str) or not isinstance(subject, str) or not subject:
            raise ValueError("Unverified provider email")
        user = _find_existing_user(email)
        if user is None:
            raise ValueError("No pre-provisioned local account")
    except Exception:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Google sign-in failed.") from None

    request.session.clear()
    request.session["user_id"] = user.user_id
    frontend = os.environ.get("LEDGER_FRONTEND_URL", "http://127.0.0.1:5173").rstrip("/")
    allowed_origins = {
        origin.strip().rstrip("/")
        for origin in os.environ.get(
            "LEDGER_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    }
    if frontend not in allowed_origins:
        frontend = sorted(allowed_origins)[0] if allowed_origins else "http://127.0.0.1:5173"
    return RedirectResponse(f"{frontend}/", status_code=303)


def _find_existing_user(email: str) -> AuthenticatedUser | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT user_id, name, email, role, cost_centre FROM users WHERE lower(email) = lower(?)",
            (email.strip(),),
        ).fetchone()
    if row is None or row["role"] not in VALID_ROLES:
        return None
    return AuthenticatedUser._from_database(row)


def _post_form(url: str, values: dict[str, str]) -> dict:
    body = urlencode(values).encode("utf-8")
    request = Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    return _read_json(request)


def _get_json(url: str, headers: dict[str, str]) -> dict:
    return _read_json(Request(url, headers=headers, method="GET"))


def _read_json(request: Request) -> dict:
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read(64 * 1024).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid provider response")
    return payload
