"""Supabase client helpers for the Flask application.

The browser never receives a service-role key. Authenticated requests use the
user's Supabase access token so database queries are evaluated by PostgreSQL
RLS policies.
"""
import os
from functools import lru_cache

from supabase import create_client, Client


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is not set")
    return value


@lru_cache(maxsize=1)
def get_public_client() -> Client:
    url = _required("SUPABASE_URL")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not key:
        raise RuntimeError("SUPABASE_PUBLISHABLE_KEY (or legacy SUPABASE_ANON_KEY) is not set")
    return create_client(url, key)


@lru_cache(maxsize=1)
def get_service_client() -> Client:
    """Server-only client for tightly controlled admin operations.

    Never pass this client or its key to browser JavaScript.
    """
    url = _required("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not set")
    return create_client(url, key)


def client_for_access_token(access_token: str) -> Client:
    """Create an isolated client for one user's JWT.

    Do not mutate the cached public client: Flask serves multiple users and a
    shared PostgREST auth header could leak one user's JWT into another user's
    request.
    """
    url = _required("SUPABASE_URL")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not key:
        raise RuntimeError("SUPABASE_PUBLISHABLE_KEY (or legacy SUPABASE_ANON_KEY) is not set")
    client = create_client(url, key)
    client.postgrest.auth(access_token)
    return client
