"""Supabase Auth ↔ Flask-Login bridge."""
from flask import session
from flask_login import login_user

from app.supabase_client import get_public_client, client_for_access_token
from app.supabase_user import SupabaseUser

ACCESS_KEY = "supabase_access_token"
REFRESH_KEY = "supabase_refresh_token"


def _load_app_user(client, auth_user_id):
    response = (
        client.table("users")
        .select("id,auth_user_id,email,first_name,last_name,phone,is_active,roles(name)")
        .eq("auth_user_id", str(auth_user_id))
        .maybe_single()
        .execute()
    )
    row = response.data
    if not row:
        return None
    role = row.get("roles") or {}
    return SupabaseUser(
        id=row["id"], auth_user_id=row["auth_user_id"], email=row["email"],
        first_name=row.get("first_name"), last_name=row.get("last_name"),
        phone=row.get("phone"), role=role.get("name"), is_active=row.get("is_active", False), raw=row,
    )


def sign_in(email: str, password: str):
    response = get_public_client().auth.sign_in_with_password({"email": email, "password": password})
    session_obj = getattr(response, "session", None)
    auth_user = getattr(response, "user", None)
    if not session_obj or not auth_user:
        return None
    session[ACCESS_KEY] = session_obj.access_token
    session[REFRESH_KEY] = session_obj.refresh_token
    user = _load_app_user(client_for_access_token(session_obj.access_token), auth_user.id)
    if not user or not user.is_active:
        session.clear()
        return None
    login_user(user, remember=False)
    return user


def sign_out():
    token = session.get(ACCESS_KEY)
    if token:
        try:
            client_for_access_token(token).auth.sign_out()
        except Exception:
            pass
    session.pop(ACCESS_KEY, None)
    session.pop(REFRESH_KEY, None)


def load_current_user(user_id):
    token = session.get(ACCESS_KEY)
    if not token:
        return None
    try:
        return _load_app_user(client_for_access_token(token), user_id)
    except Exception:
        return None
