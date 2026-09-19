"""Supabase data-access layer for the LMPS application.

This module deliberately keeps Supabase/PostgREST details out of Flask
blueprints. All requests made with a user's access token remain subject to
Supabase RLS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from types import SimpleNamespace
from flask import session

from app.supabase_client import client_for_access_token


class SupabaseDataError(RuntimeError):
    pass


def _token() -> str:
    from app.supabase_auth import current_access_token\n    token = current_access_token()
    if not token:
        raise SupabaseDataError("Your Supabase session has expired. Please sign in again.")
    return token


def _client():
    return client_for_access_token(_token())


def _first(response):
    data = getattr(response, "data", None)
    if isinstance(data, list):
        return data[0] if data else None
    return data


def _rows(response):
    data = getattr(response, "data", None)
    return data if isinstance(data, list) else ([] if data is None else [data])


def _obj(row: dict[str, Any] | None):
    return SimpleNamespace(**row) if row else None


@dataclass
class Pagination:
    items: list[Any]
    page: int
    per_page: int
    total: int

    @property
    def pages(self):
        return max((self.total + self.per_page - 1) // self.per_page, 1)

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def next_num(self):
        return self.page + 1


@dataclass
class TeacherContext:
    profile: Any
    assignments: list[Any] = field(default_factory=list)


class LMPSRepository:
    def __init__(self):
        self.client = _client()

    def current_user(self):
        from flask_login import current_user
        return current_user

    def teacher_context(self) -> TeacherContext | None:
        user = self.current_user()
        res = (
            self.client.table("teacher_profiles")
            .select("id,user_id,staff_id,employee_number,qualification,specialization,date_joined,is_active")
            .eq("user_id", user.id)
            .eq("is_active", True)
            .maybe_single()
            .execute()
        )
        profile = _first(res)
        if not profile:
            return None
        assignments = _rows(
            self.client.table("teacher_assignments")
            .select("id,teacher_id,subject_id,class_id,academic_year_id,term_id,subjects(id,code,name),classes(id,name),academic_years(id,name),terms(id,name)")
            .eq("teacher_id", profile["id"])
            .execute()
        )
        return TeacherContext(_obj(profile), [self._assignment(a) for a in assignments])

    @staticmethod
    def _assignment(row):
        out = dict(row)
        out["subject"] = _obj(out.pop("subjects", None))
        out["class_"] = _obj(out.pop("classes", None))
        out["academic_year"] = _obj(out.pop("academic_years", None))
        out["term"] = _obj(out.pop("terms", None))
        return _obj(out)

    def academic_years(self):
        return [_obj(x) for x in _rows(self.client.table("academic_years").select("id,name,start_date,end_date,is_current").order("name", desc=True).execute())]

    def terms(self):
        return [_obj(x) for x in _rows(self.client.table("terms").select("id,academic_year_id,name,term_number,start_date,end_date,is_current").order("term_number").execute())]

    def classes(self):
        return [_obj(x) for x in _rows(self.client.table("classes").select("id,name,level,description,is_active").eq("is_active", True).order("name").execute())]

    def subjects(self):
        return [_obj(x) for x in _rows(self.client.table("subjects").select("id,code,name,description,is_active").eq("is_active", True).order("name").execute())]

    def _plan_select(self):
        return (
            "id,reference,teacher_assignment_id,academic_year_id,term_id,class_id,subject_id,week_number,week_start_date,status,current_version_id,submitted_at,approved_at,rejected_at,created_at,updated_at,"
            "classes(id,name),subjects(id,code,name),learner_plan_versions(id,learner_plan_id,version_number,content,created_by,created_at),"
            "teacher_assignments!inner(id,teacher_id,subject_id,class_id,academic_year_id,term_id)"
        )

    def list_teacher_plans(self, teacher_id: str, status: str | None = None, search: str = "", page: int = 1, per_page: int = 10) -> Pagination:
        query = self.client.table("learner_plans").select(self._plan_select(), count="exact").eq("teacher_assignments.teacher_id", teacher_id)
        if status:
            query = query.eq("status", status)
        if search:
            query = query.ilike("reference", f"%{search}%")
        start = (page - 1) * per_page
        response = query.order("updated_at", desc=True).range(start, start + per_page - 1).execute()
        rows = [self._plan(x) for x in _rows(response)]
        total = getattr(response, "count", None)
        if total is None:
            total = len(rows)
        return Pagination(rows, page, per_page, total)

    def get_plan(self, plan_id: str, teacher_id: str | None = None):
        query = self.client.table("learner_plans").select(self._plan_select()).eq("id", str(plan_id))
        if teacher_id:
            query = query.eq("teacher_assignments.teacher_id", teacher_id)
        row = _first(query.maybe_single().execute())
        return self._plan(row) if row else None

    def _plan(self, row):
        if not row:
            return None
        out = dict(row)
        out["class_"] = _obj(out.pop("classes", None))
        out["subject"] = _obj(out.pop("subjects", None))
        versions = []
        for v in out.pop("learner_plan_versions", []) or []:
            content = v.get("content") or {}
            vv = dict(v)
            vv.update(content)
            vv["status"] = out.get("status") if v.get("id") == out.get("current_version_id") else vv.get("status", "")
            vv["comments"] = []
            vv["submitter"] = None
            versions.append(_obj(vv))
        out["versions"] = sorted(versions, key=lambda x: x.version_number)
        out["current_version"] = next((v for v in out["versions"] if v.id == out.get("current_version_id")), None)
        out["week"] = out.pop("week_number")
        out["current_status"] = out.pop("status")
        out["teacher_assignment"] = _obj(out.pop("teacher_assignments", None))
        return _obj(out)

    def create_plan(self, teacher_assignment_id: str, academic_year_id: str, term_id: str, class_id: str, subject_id: str, week: int):
        year = _first(self.client.table("academic_years").select("id,name").eq("id", academic_year_id).maybe_single().execute())
        token = (year or {}).get("name", "2026")[:4]
        existing = _rows(self.client.table("learner_plans").select("reference").eq("academic_year_id", academic_year_id).execute())
        reference = f"LP-{token}-{len(existing)+1:04d}"
        plan = _first(self.client.table("learner_plans").insert({
            "reference": reference,
            "teacher_assignment_id": teacher_assignment_id,
            "academic_year_id": academic_year_id,
            "term_id": term_id,
            "class_id": class_id,
            "subject_id": subject_id,
            "week_number": week,
            "status": "DRAFT",
        }).select("id,reference,current_version_id").single().execute())
        version = _first(self.client.table("learner_plan_versions").insert({
            "learner_plan_id": plan["id"], "version_number": 1, "content": {}, "created_by": self.current_user().id
        }).select("id").single().execute())
        self.client.table("learner_plans").update({"current_version_id": version["id"]}).eq("id", plan["id"]).execute()
        return self.get_plan(plan["id"])

    def save_version(self, plan_id: str, content: dict[str, Any]):
        plan = self.get_plan(plan_id)
        if not plan or plan.current_status != "DRAFT":
            raise SupabaseDataError("Only a DRAFT plan can be edited directly.")
        self.client.table("learner_plan_versions").update({"content": content}).eq("id", plan.current_version_id).eq("learner_plan_id", plan_id).execute()
        return self.get_plan(plan_id)

    def submit(self, plan_id: str, resubmit=False):
        plan = self.get_plan(plan_id)
        target = "RESUBMITTED" if resubmit else "SUBMITTED"
        allowed = ("CORRECTION_REQUIRED",) if resubmit else ("DRAFT",)
        if not plan or plan.current_status not in allowed:
            raise SupabaseDataError("This plan is not ready for submission.")
        content = (plan.current_version and plan.current_version.__dict__) or {}
        required = ["topic", "content_standard", "indicator", "learning_objectives", "activities"]
        missing = [x for x in required if not content.get(x)]
        if missing:
            raise SupabaseDataError("The following fields are required: " + ", ".join(missing))
        self.client.table("learner_plans").update({"status": target}).eq("id", plan_id).select("id").single().execute()
        return self.get_plan(plan_id)

    def resubmit(self, plan_id: str, content: dict[str, Any]):
        plan = self.get_plan(plan_id)
        if not plan or plan.current_status != "CORRECTION_REQUIRED":
            raise SupabaseDataError("This plan is not awaiting correction.")
        next_no = max([v.version_number for v in plan.versions] or [0]) + 1
        version = _first(self.client.table("learner_plan_versions").insert({
            "learner_plan_id": plan_id, "version_number": next_no, "content": content, "created_by": self.current_user().id
        }).select("id").single().execute())
        self.client.table("learner_plans").update({"current_version_id": version["id"], "status": "RESUBMITTED"}).eq("id", plan_id).execute()
        return self.get_plan(plan_id)

    def delete_draft(self, plan_id: str):
        plan = self.get_plan(plan_id)
        if not plan or plan.current_status != "DRAFT":
            raise SupabaseDataError("Only a DRAFT plan can be deleted.")
        self.client.table("learner_plans").delete().eq("id", plan_id).execute()

    def unread_notifications(self):
        rows = _rows(self.client.table("notifications").select("*").eq("recipient_user_id", self.current_user().id).eq("is_read", False).order("created_at", desc=True).execute())
        return [_obj(x) for x in rows]

    def recent_notifications(self, limit=5):
        rows = _rows(self.client.table("notifications").select("*").eq("recipient_user_id", self.current_user().id).order("created_at", desc=True).limit(limit).execute())
        return [_obj(x) for x in rows]


def repo():
    return LMPSRepository()
