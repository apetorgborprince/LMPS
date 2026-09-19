"""Supabase Auth bridge with server-side token storage."""
from datetime import datetime, timezone

from flask import current_app, session
from flask_login import login_user

from app.supabase_client import client_for_access_token, get_public_client
from app.supabase_user import SupabaseUser

SESSION_ID_KEY = "lmps_session_id"


def _store():
    return current_app.extensions["lmps_token_store"]


def _tokens():
    return _store().get(session.get(SESSION_ID_KEY)) or {}


def _session_expiry(session_obj):
    value = getattr(session_obj, "expires_at", None)
    if value is None:
        return datetime.now(timezone.utc).timestamp() + 3600
    try:
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return datetime.now(timezone.utc).timestamp() + 3600


def _refresh_if_needed(sid, tokens):
    if not sid or not tokens:
        return tokens
    expires = tokens.get("expires_at")
    try:
        expiry = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
        needs_refresh = expiry <= datetime.now(timezone.utc)
    except (TypeError, ValueError):
        needs_refresh = False

    if not needs_refresh:
        return tokens

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        _store().delete(sid)
        return {}

    try:
        response = get_public_client().auth.refresh_session(refresh_token)
        refreshed = getattr(response, "session", None)
        if not refreshed:
            _store().delete(sid)
            return {}
        updated = {
            "access_token": refreshed.access_token,
            "refresh_token": refreshed.refresh_token,
            "auth_user_id": tokens.get("auth_user_id"),
            "expires_at": _session_expiry(refreshed),
        }
        _store().save(sid, updated)
        return updated
    except Exception:
        _store().delete(sid)
        return {}


def current_access_token():
    sid = session.get(SESSION_ID_KEY)
    return _refresh_if_needed(sid, _store().get(sid) or {}).get("access_token")


def _load_app_user(client, auth_user_id):
    row = (
        client.table("users")
        .select("id,auth_user_id,email,first_name,last_name,phone,is_active,roles(name)")
        .eq("auth_user_id", str(auth_user_id))
        .maybe_single()
        .execute()
    ).data
    if not row:
        return None
    role = row.get("roles") or {}
    return SupabaseUser(
        id=row["id"],
        auth_user_id=row["auth_user_id"],
        email=row["email"],
        first_name=row.get("first_name") or "",
        last_name=row.get("last_name") or "",
        phone=row.get("phone"),
        role=role.get("name"),
        is_active=row.get("is_active", False),
        raw=row,
    )


def sign_in(email, password):
    response = get_public_client().auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    supabase_session = getattr(response, "session", None)
    auth_user = getattr(response, "user", None)
    if not supabase_session or not auth_user:
        return None

    payload = {
        "access_token": supabase_session.access_token,
        "refresh_token": supabase_session.refresh_token,
        "auth_user_id": auth_user.id,
        "expires_at": _session_expiry(supabase_session),
    }
    sid = _store().create(payload)
    session.clear()
    session[SESSION_ID_KEY] = sid

    user = _load_app_user(
        client_for_access_token(supabase_session.access_token), auth_user.id
    )
    if not user or not user.is_active:
        _store().delete(sid)
        session.clear()
        return None
    login_user(user, remember=False)
    return user


def sign_out():
    sid = session.get(SESSION_ID_KEY)
    token = current_access_token()
    if token:
        try:
            client_for_access_token(token).auth.sign_out()
        except Exception:
            pass
    _store().delete(sid)
    session.clear()


def load_current_user(user_id):
    token = current_access_token()
    if not token:
        return None
    try:
        return _load_app_user(client_for_access_token(token), user_id)
    except Exception:
        return None
