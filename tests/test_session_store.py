from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def test_db11_session_migration_is_present_and_locks_down_rls():
    sql = (ROOT / "supabase" / "migrations" / "DB-11-app-sessions.sql").read_text(
        encoding="utf-8"
    )
    assert "create table if not exists public.app_sessions" in sql
    assert "alter table public.app_sessions enable row level security" in sql
    assert "revoke all on public.app_sessions from anon, authenticated" in sql


def test_session_store_supports_database_backend():
    source = (ROOT / "app" / "session_store.py").read_text(encoding="utf-8")
    assert 'SESSION_STORE", "filesystem"' in source
    assert 'self.backend == "database"' in source
    assert 'table("app_sessions")' in source


def test_auth_refreshes_expired_server_side_sessions():
    source = (ROOT / "app" / "supabase_auth.py").read_text(encoding="utf-8")
    assert "refresh_session" in source
    assert "current_access_token" in source
    assert "refresh_token" in source
