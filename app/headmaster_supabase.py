"""Supabase repository for Headmaster review workflow."""
from types import SimpleNamespace
from app.data_supabase import _client, _rows, _first, _obj, SupabaseDataError


def _plan(row):
    if not row:
        return None
    out = dict(row)
    out["class_"] = _obj(out.pop("classes", None))
    out["subject"] = _obj(out.pop("subjects", None))
    ta = out.pop("teacher_assignments", None)
    out["teacher_assignment"] = _obj(ta)
    teacher = (ta or {}).get("teacher_profiles") or {}
    user = (teacher.get("users") or {})
    out["teacher"] = _obj({"id": teacher.get("id"), "user": _obj(user), "staff_id": teacher.get("staff_id")})
    versions = []
    for v in out.pop("learner_plan_versions", []) or []:
        vv = dict(v)
        vv.update(vv.get("content") or {})
        versions.append(_obj(vv))
    out["versions"] = sorted(versions, key=lambda x: x.version_number)
    out["current_version"] = next((v for v in out["versions"] if str(v.id) == str(out.get("current_version_id"))), None)
    out["week"] = out.pop("week_number")
    out["current_status"] = out.pop("status")
    return _obj(out)


def _select():
    return (
        "id,reference,teacher_assignment_id,academic_year_id,term_id,class_id,subject_id,"
        "week_number,week_start_date,status,current_version_id,submitted_at,approved_at,rejected_at,created_at,updated_at,"
        "classes(id,name),subjects(id,code,name),"
        "teacher_assignments!inner(id,teacher_id,subject_id,class_id,academic_year_id,term_id,"
        "teacher_profiles!inner(id,user_id,staff_id,users!inner(id,first_name,last_name,email))) ,"
        "learner_plan_versions(id,learner_plan_id,version_number,content,created_by,created_at)"
    )


class HeadmasterRepository:
    def __init__(self):
        self.client = _client()

    def profile(self):
        from flask_login import current_user
        row = _first(self.client.table("headmaster_profiles").select(
            "id,user_id,staff_id,appointment_date,is_active,school_id,schools(id,school_name,school_code)"
        ).eq("user_id", current_user.id).eq("is_active", True).maybe_single().execute())
        if not row:
            return None
        return _obj(row)

    def _plans(self, status=None, limit=100):
        q = self.client.table("learner_plans").select(_select()).order("updated_at", desc=False).limit(limit)
        if status:
            q = q.eq("status", status)
        rows = _rows(q.execute())
        return [_plan(r) for r in rows]

    def pending(self):
        return self._plans("SUBMITTED") + self._plans("RESUBMITTED")

    def approved(self):
        return self._plans("APPROVED")

    def rejected(self):
        return self._plans("REJECTED")

    def counts(self):
        return {
            "total_teachers": len(_rows(self.client.table("teacher_profiles").select("id").eq("is_active", True).execute())),
            "pending_approval": len(self.pending()),
            "approved": len(self.approved()),
            "rejected": len(self.rejected()),
        }

    def get_plan(self, plan_id):
        row = _first(self.client.table("learner_plans").select(_select()).eq("id", str(plan_id)).maybe_single().execute())
        plan = _plan(row)
        if not plan:
            return None
        comments = _rows(self.client.table("plan_comments").select(
            "id,learner_plan_id,version_id,author_id,comment,created_at,users(id,first_name,last_name,email)"
        ).eq("learner_plan_id", str(plan_id)).order("created_at").execute())
        by_version = {}
        for c in comments:
            user = c.pop("users", None) or {}
            c["author"] = _obj({"id": user.get("id"), "full_name": f"{user.get('first_name','')} {user.get('last_name','')}".strip()})
            by_version.setdefault(str(c["version_id"]), []).append(_obj(c))
        for v in plan.versions:
            v.comments = by_version.get(str(v.id), [])
        return plan

    def decide(self, plan_id, decision, comment):
        plan = self.get_plan(plan_id)
        if not plan or plan.current_status not in ("SUBMITTED", "RESUBMITTED"):
            raise SupabaseDataError("This learner plan is not currently awaiting Headmaster review.")
        if decision not in ("APPROVED", "REJECTED", "CORRECTION_REQUIRED"):
            raise SupabaseDataError("Invalid review decision.")
        user_id = self._current_user_id()
        if comment:
            self.client.table("plan_comments").insert({
                "learner_plan_id": str(plan_id),
                "version_id": str(plan.current_version_id),
                "author_id": user_id,
                "comment": comment.strip(),
            }).execute()
        self.client.table("plan_reviews").insert({
            "learner_plan_id": str(plan_id),
            "version_id": str(plan.current_version_id),
            "reviewer_id": user_id,
            "decision": decision,
            "comments": comment.strip() if comment else None,
        }).execute()
        self.client.table("learner_plans").update({"status": decision}).eq("id", str(plan_id)).eq("current_version_id", str(plan.current_version_id)).execute()
        return self.get_plan(plan_id)

    def _current_user_id(self):
        from flask_login import current_user
        return str(current_user.id)
