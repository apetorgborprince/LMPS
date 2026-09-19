from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.utils.decorators import require_role
from app.utils.audit import log_action
from app.headmaster_supabase import HeadmasterRepository
from app.data_supabase import SupabaseDataError
from app.blueprints.headmaster.forms import ApproveForm, RejectForm, RequestCorrectionForm

headmaster_bp = Blueprint("headmaster", __name__, url_prefix="/headmaster", template_folder="../../templates/headmaster")


def _repo():
    return HeadmasterRepository()


def _plan_or_404(plan_id):
    plan = _repo().get_plan(plan_id)
    if not plan:
        abort(404)
    return plan


@headmaster_bp.route("/dashboard")
@login_required
@require_role("HEADMASTER")
def dashboard():
    return render_template("headmaster/dashboard.html", counts=_repo().counts())


@headmaster_bp.route("/pending-approval")
@login_required
@require_role("HEADMASTER")
def pending_approval():
    return render_template("headmaster/plan_list.html", plans=_repo().pending(), title="Pending Approval")


@headmaster_bp.route("/approved")
@login_required
@require_role("HEADMASTER")
def approved_plans():
    return render_template("headmaster/plan_list.html", plans=_repo().approved(), title="Approved Plans")


@headmaster_bp.route("/rejected")
@login_required
@require_role("HEADMASTER")
def rejected_plans():
    return render_template("headmaster/plan_list.html", plans=_repo().rejected(), title="Rejected Plans")


@headmaster_bp.route("/plans/<plan_id>", methods=["GET", "POST"])
@login_required
@require_role("HEADMASTER")
def review_plan(plan_id):
    plan = _plan_or_404(plan_id)
    approve_form = ApproveForm(prefix="approve")
    reject_form = RejectForm(prefix="reject")
    correction_form = RequestCorrectionForm(prefix="correction")

    try:
        if correction_form.submit.data and correction_form.validate_on_submit():
            _repo().decide(plan.id, "CORRECTION_REQUIRED", correction_form.comment.data)
            log_action(current_user.id, "REQUEST_CORRECTION", "learner_plan", plan.id)
            flash(f"Correction requested on {plan.reference}.", "success")
            return redirect(url_for("headmaster.review_plan", plan_id=plan.id))

        if approve_form.submit.data and approve_form.validate_on_submit():
            _repo().decide(plan.id, "APPROVED", "Approved by Headmaster.")
            log_action(current_user.id, "APPROVE_PLAN", "learner_plan", plan.id)
            flash(f"{plan.reference} approved.", "success")
            return redirect(url_for("headmaster.review_plan", plan_id=plan.id))

        if reject_form.submit.data and reject_form.validate_on_submit():
            _repo().decide(plan.id, "REJECTED", reject_form.reason.data)
            log_action(current_user.id, "REJECT_PLAN", "learner_plan", plan.id)
            flash(f"{plan.reference} rejected.", "success")
            return redirect(url_for("headmaster.review_plan", plan_id=plan.id))
    except SupabaseDataError as exc:
        flash(str(exc), "error")

    actionable = plan.current_status in ("SUBMITTED", "RESUBMITTED")
    return render_template("headmaster/plan_review.html", plan=plan, actionable=actionable,
                           approve_form=approve_form, reject_form=reject_form, correction_form=correction_form)
