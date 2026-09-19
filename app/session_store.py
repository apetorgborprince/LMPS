"""Server-side session token storage.

Filesystem storage remains available for local development. Database storage is
recommended for Vercel/serverless deployments because the filesystem is ephemeral.
"""
import json
import os
import secrets
from pathlib import Path


class TokenStore:
    def __init__(self, directory):
        self.backend = os.environ.get("SESSION_STORE", "filesystem").lower()
        self.directory = Path(directory)
        if self.backend == "filesystem":
            self.directory.mkdir(parents=True, exist_ok=True)

    def create(self, payload):
        sid = secrets.token_urlsafe(32)
        self.save(sid, payload)
        return sid

    def save(self, sid, payload):
        if self.backend == "database":
            self._db_upsert(sid, payload)
            return
        path = self.directory / f"{sid}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(tmp, path)

    def get(self, sid):
        if not sid:
            return None
        if self.backend == "database":
            return self._db_get(sid)
        try:
            return json.loads(
                (self.directory / f"{sid}.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return None

    def delete(self, sid):
        if not sid:
            return
        if self.backend == "database":
            self._db_delete(sid)
            return
        try:
            (self.directory / f"{sid}.json").unlink()
        except FileNotFoundError:
            pass

    def _service(self):
        from app.supabase_client import get_service_client
        return get_service_client()

    def _db_upsert(self, sid, payload):
        self._service().table("app_sessions").upsert(
            {
                "session_id": sid,
                "auth_user_id": payload["auth_user_id"],
                "access_token": payload["access_token"],
                "refresh_token": payload["refresh_token"],
                "expires_at": payload["expires_at"],
            },
            on_conflict="session_id",
        ).execute()

    def _db_get(self, sid):
        response = (
            self._service()
            .table("app_sessions")
            .select("session_id,auth_user_id,access_token,refresh_token,expires_at")
            .eq("session_id", sid)
            .maybe_single()
            .execute()
        )
        row = getattr(response, "data", None)
        if not row:
            return None
        return row

    def _db_delete(self, sid):
        self._service().table("app_sessions").delete().eq("session_id", sid).execute()
