-- DB-11: persistent application sessions for serverless deployment.
-- Run this migration in the LMPS Supabase SQL editor before enabling
-- SESSION_STORE=database in Vercel.

create table if not exists public.app_sessions (
    id uuid primary key default gen_random_uuid(),
    session_id text not null unique,
    auth_user_id uuid not null,
    access_token text not null,
    refresh_token text not null,
    expires_at timestamptz not null,
    created_at timestamptz not null default now(),
    last_used_at timestamptz not null default now()
);

create index if not exists app_sessions_expires_at_idx
    on public.app_sessions (expires_at);

create index if not exists app_sessions_auth_user_id_idx
    on public.app_sessions (auth_user_id);

alter table public.app_sessions enable row level security;

revoke all on public.app_sessions from anon, authenticated;

create or replace function private.cleanup_expired_app_sessions()
returns integer
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    deleted_count integer;
begin
    delete from public.app_sessions
    where expires_at < now();
    get diagnostics deleted_count = row_count;
    return deleted_count;
end;
$$;

revoke all on function private.cleanup_expired_app_sessions() from public, anon, authenticated;
