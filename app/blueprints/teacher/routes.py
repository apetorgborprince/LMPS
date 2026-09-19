from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.utils.decorators import require_role
from app.utils.audit import log_action
from app.data_supabase import repo, SupabaseDataError
from app.blueprints.teacher.forms import NewPlanForm, PlanContentForm, UploadForm

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher", template_folder="../../templates/teacher")


def _context_or_403():
    context = repo().teacher_context()
    if not context:
        abort(403)
    return context


def _own_plan_or_404(plan_id):
    context = _context_or_403()
    plan = repo().get_plan(plan_id, str(context.profile.id))
    if not plan:
        abort(404)
    return plan


def _content(form):
    return {
        "topic": form.topic.data,
        "sub_strand": form.sub_strand.data,
        "content_standard": form.content_standard.data,
        "indicator": form.indicator.data,
        "learning_objectives": form.learning_objectives.data,
        "resources": form.resources.data,
        "activities": form.activities.data,
        "assessment": form.assessment.data,
        "references_text": form.references_text.data,
        "remarks": form.remarks.data,
    }


@teacher_bp.route("/dashboard")
@login_required
@require_role("TEACHER")
def dashboard():
    context = _context_or_403()
    r = repo()
    pagination = r.list_teacher_plans(str(context.profile.id), page=1, per_page=50)
    plans = pagination.items
    statuses = [p.current_status for p in plans]
    counts = {
        "total": pagination.total,
        "draft": statuses.count("DRAFT"),
        "submitted": sum(s in ("SUBMITTED", "RESUBMITTED") for s in statuses),
        "correction_required": statuses.count("CORRECTION_REQUIRED"),
        "approved": statuses.count("APPROVED"),
        "rejected": statuses.count("REJECTED"),
    }
    return render_template("teacher/dashboard.html", counts=counts, notifications=r.recent_notifications(5))


@teacher_bp.route("/plans")
@login_required
@require_role("TEACHER")
def list_plans():
    context = _context_or_403()
    status_filter = request.args.get("status")
    search = request.args.get("q", "").strip()
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 10, type=int), 5), 50)
    pagination = repo().list_teacher_plans(str(context.profile.id), status_filter, search, page, per_page)
    return render_template("teacher/plan_list.html", plans=pagination.items, pagination=pagination,
                           status_filter=status_filter, search=search, subject_id=None, class_id=None)


@teacher_bp.route("/plans/new", methods=["GET", "POST"])
@login_required
@require_role("TEACHER")
def new_plan():
    context = _context_or_403()
    r = repo()
    form = NewPlanForm()
    years = r.academic_years()
    terms = r.terms()
    form.academic_year_id.choices = [(str(y.id), y.name) for y in years]
    form.term_id.choices = [(str(t.id), t.name) for t in terms]
    form.class_id.choices = sorted({(str(a.class_id), a.class_.name) for a in context.assignments}, key=lambda x: x[1])
    form.subject_id.choices = sorted({(str(a.subject_id), a.subject.name) for a in context.assignments}, key=lambda x: x[1])

    if form.validate_on_submit():
        assignment = next((a for a in context.assignments if str(a.class_id) == form.class_id.data and str(a.subject_id) == form.subject_id.data
                           and str(a.academic_year_id) == form.academic_year_id.data
                           and (not form.term_id.data or not a.term_id or str(a.term_id) == form.term_id.data)), None)
        if not assignment:
            flash("You are not assigned to that class and subject for the selected academic period.", "error")
            return render_template("teacher/new_plan.html", form=form)
        try:
            plan = r.create_plan(str(assignment.id), form.academic_year_id.data, form.term_id.data,
                                 form.class_id.data, form.subject_id.data, form.week.data)
            log_action(current_user.id, "CREATE_PLAN_DRAFT", "learner_plan", plan.id)
            flash(f"Draft {plan.reference} created.", "success")
            return redirect(url_for("teacher.edit_plan", plan_id=plan.id))
        except Exception as exc:
            flash(str(exc), "error")
    return render_template("teacher/new_plan.html", form=form)


@teacher_bp.route("/plans/<plan_id>", methods=["GET", "POST"])
@login_required
@require_role("TEACHER")
def edit_plan(plan_id):
    plan = _own_plan_or_404(plan_id)
    version = plan.current_version
    editable = plan.current_status in ("DRAFT", "CORRECTION_REQUIRED")
    if not editable:
        return render_template("teacher/plan_detail_readonly.html", plan=plan)

    form = PlanContentForm(obj=version)
    upload_form = UploadForm()
    if form.validate_on_submit():
        try:
            content = _content(form)
            if plan.current_status == "DRAFT":
                repo().save_version(plan.id, content)
                if form.submit_for_review.data:
                    repo().submit(plan.id)
                    log_action(current_user.id, "SUBMIT_PLAN", "learner_plan", plan.id)
                    flash(f"{plan.reference} submitted for review.", "success")
                else:
                    log_action(current_user.id, "SAVE_DRAFT", "learner_plan", plan.id)
                    flash("Draft saved.", "success")
            else:
                if form.submit_for_review.data:
                    repo().resubmit(plan.id, content)
                    log_action(current_user.id, "RESUBMIT_PLAN", "learner_plan", plan.id)
                    flash(f"{plan.reference} resubmitted for review.", "success")
                else:
                    flash("Corrections must be resubmitted, not saved as a separate draft.", "info")
        except SupabaseDataError as exc:
            flash(str(exc), "error")
        except Exception:
            flash("The plan could not be saved. Please try again.", "error")
        return redirect(url_for("teacher.edit_plan", plan_id=plan.id))

    previous_version = None
    if plan.current_status == "CORRECTION_REQUIRED" and len(plan.versions) >= 2:
        previous_version = plan.versions[-2]
    return render_template("teacher/plan_form.html", plan=plan, form=form, upload_form=upload_form,
                           previous_version=previous_version)


@teacher_bp.route("/plans/<plan_id>/upload", methods=["POST"])
@login_required
@require_role("TEACHER")
def upload_document(plan_id):
    plan = _own_plan_or_404(plan_id)
    if plan.current_status not in ("DRAFT", "CORRECTION_REQUIRED"):
        abort(403)
    flash("Document storage is being migrated to Supabase Storage.", "info")
    return redirect(url_for("teacher.edit_plan", plan_id=plan.id))


@teacher_bp.route("/plans/<plan_id>/delete", methods=["POST"])
@login_required
@require_role("TEACHER")
def delete_draft(plan_id):
    plan = _own_plan_or_404(plan_id)
    try:
        repo().delete_draft(plan.id)
        log_action(current_user.id, "DELETE_DRAFT", "learner_plan", plan.id)
        flash("Draft deleted.", "info")
    except SupabaseDataError:
        abort(403)
    return redirect(url_for("teacher.list_plans"))
