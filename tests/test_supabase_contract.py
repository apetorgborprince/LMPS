from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_required_supabase_files_exist():
 for p in ["app/supabase_client.py","app/supabase_auth.py","app/supabase_user.py","app/data_supabase.py","app/admin_supabase.py","app/headmaster_supabase.py","app/siso_supabase.py","app/session_store.py"]:assert (ROOT/p).exists(),p
def test_required_storage_and_workflow_strings_exist():
 assert "learner-plan-attachments" in (ROOT/"app/blueprints/teacher/routes.py").read_text();assert "CORRECTION_REQUIRED" in (ROOT/"app/headmaster_supabase.py").read_text();assert "siso_monitoring_visits" in (ROOT/"app/siso_supabase.py").read_text()
