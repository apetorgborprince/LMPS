# LMPS Supabase setup

## Environment
Set SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_SERVICE_ROLE_KEY, SECRET_KEY, and a private persistent SESSION_TOKEN_DIR. Never expose the service-role key to the browser.

## First administrator
Create the first Auth user using the Supabase dashboard or server-side admin API, then create its public.users row with the ADMIN role. Subsequent accounts can be provisioned from Admin > Users > Create user.

## School configuration
1. Admin > Schools
2. Admin > Academic Years
3. Admin > Terms
4. Admin > Workflow Settings
5. Admin > Users
6. Admin > Teacher Assignments
7. Admin > SISO Assignments

## End-to-end test
Teacher creates and submits a plan -> Headmaster approves, rejects, or requests correction -> Teacher resubmits if needed -> SISO sees approved plans, records visits, observations and action points -> verify notifications and audit logs.

## Storage
The private learner-plan-attachments bucket accepts PDF/DOC/DOCX files up to 10 MB.