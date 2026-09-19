# LMPS — Learner Plan Management System

Supabase migration in progress.

Target workflow: TEACHER → HEADMASTER → SISO

System administration role: ADMIN

This repository is being migrated from the legacy SQLAlchemy/local-auth architecture to Supabase Auth + PostgreSQL with Row Level Security.

## Migration status
- DB-01 to DB-09: Supabase database foundation completed
- DB-10: Flask/Supabase integration in progress
- HOD: removed from the target workflow and database roles

Do not place Supabase service-role keys or other secrets in this repository.
