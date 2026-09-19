from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding="utf-8")
def test_target_roles_and_workflow_are_documented():
 readme=read("README.md");assert all(x in readme for x in ["ADMIN","TEACHER","HEADMASTER","SISO"]);assert "TEACHER → HEADMASTER → SISO" in readme
def test_active_blueprints_do_not_use_sqlalchemy_models():
 for path in ["app/blueprints/admin/routes.py","app/blueprints/headmaster/routes.py","app/blueprints/siso/routes.py","app/blueprints/teacher/routes.py","app/blueprints/notifications/routes.py","app/blueprints/files/routes.py"]:
  source=read(path);assert "db.session" not in source;assert "LearnerPlan.query" not in source;assert "TeacherProfile.query" not in source
def test_hod_is_not_an_active_role_reference():
 active="\n".join(read(p) for p in ["app/__init__.py","app/config.py","app/blueprints/admin/routes.py","app/blueprints/headmaster/routes.py","app/blueprints/siso/routes.py","app/blueprints/teacher/routes.py"]);assert "HOD" not in active
def test_server_side_token_store_is_used():
 auth=read("app/supabase_auth.py");init=read("app/__init__.py");assert "TokenStore" in init;assert "SESSION_ID_KEY" in auth;assert "supabase_access_token" not in auth
