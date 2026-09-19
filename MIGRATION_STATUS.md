# LMPS Migration Status

## Completed database phases

- DB-01 — Foundation
- DB-02 — Teacher structure
- DB-03 — Learner plans and versions
- DB-04 — Headmaster/SISO structure
- DB-05 — Supabase Auth/RBAC foundation
- DB-06 — Row Level Security
- DB-07 — Learner-plan workflow integrity
- DB-08 — Notifications
- DB-09 — SISO monitoring/reporting hardening

## DB-10 application migration

The Flask application is being migrated from the legacy SQLAlchemy/local-auth architecture to:

Flask UI → Supabase data layer → Supabase Auth → PostgreSQL/RLS

Teacher learner-plan operations have been moved to the Supabase data layer. Headmaster, SISO, Admin, reporting, files, and remaining legacy services still require migration before the application is considered complete.

## Target workflow

TEACHER → HEADMASTER → SISO

ADMIN is the system administration role.

HOD is not part of the target architecture.
