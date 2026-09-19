from flask import Blueprint,render_template,redirect,url_for,flash,request
from flask_login import login_required,current_user
from app.utils.decorators import require_role
from app.utils.audit import log_action
from app.admin_supabase import AdminRepository
from app.blueprints.admin.forms import CreateUserForm,ClassForm,SubjectForm,AcademicYearForm,TermForm,DeadlineForm,TeacherAssignmentForm,WorkflowSettingsForm,SchoolForm,SISOAssignmentForm
admin_bp=Blueprint("admin",__name__,url_prefix="/admin",template_folder="../../templates/admin")
def repo():return AdminRepository()
def fail(e):flash(str(e),"error")
@admin_bp.route("/dashboard")
@login_required
@require_role("ADMIN")
def dashboard():return render_template("admin/dashboard.html",counts=repo().counts())
@admin_bp.route("/users")
@login_required
@require_role("ADMIN")
def users():return render_template("admin/users.html",users=repo().users())
@admin_bp.route("/users/new",methods=["GET","POST"])
@login_required
@require_role("ADMIN")
def new_user():
 form=CreateUserForm()
 if form.validate_on_submit():
  try:u,temp=repo().create_user(form.email.data.lower().strip(),form.full_name.data,form.role.data,form.phone.data,form.staff_id.data or None);log_action(current_user.id,"CREATE_USER","User",u.id);flash(f"User {u.email} created. Temporary password: {temp}","success");return redirect(url_for("admin.users"))
  except Exception as e:fail(e)
 return render_template("admin/new_user.html",form=form)
@admin_bp.route("/users/<user_id>/toggle-active",methods=["POST"])
@login_required
@require_role("ADMIN")
def toggle_active(user_id):
 try:
  u=next((x for x in repo().users() if str(x.id)==str(user_id)),None)
  if not u:return ("Not found",404)
  u=repo().set_active(user_id,not u.is_active_user);log_action(current_user.id,"TOGGLE_USER_ACTIVE","User",u.id);flash(f"{u.email} is now {'active' if u.is_active_user else 'deactivated'}.","success")
 except Exception as e:fail(e)
 return redirect(url_for("admin.users"))
@admin_bp.route("/users/<user_id>/reset-password",methods=["POST"])
@login_required
@require_role("ADMIN")
def reset_password(user_id):
 try:p=repo().reset_password(user_id);log_action(current_user.id,"ADMIN_RESET_PASSWORD","User",user_id);flash(f"New temporary password: {p}","success")
 except Exception as e:fail(e)
 return redirect(url_for("admin.users"))
@admin_bp.route("/schools",methods=["GET","POST"])
@login_required
@require_role("ADMIN")
def schools():
 r=repo();form=SchoolForm()
 if form.validate_on_submit():
  try:r.add_school(form.school_name.data,form.school_code.data,form.circuit.data,form.district.data);log_action(current_user.id,"CREATE_SCHOOL","School");flash("School added.","success")
  except Exception as e:fail(e)
 return render_template("admin/schools.html",form=form,schools=r.schools())
@admin_bp.route("/siso-assignments",methods=["GET","POST"])
@login_required
@require_role("ADMIN")
def siso_assignments():
 r=repo();form=SISOAssignmentForm();form.siso_id.choices=[(str(x.id),f"{x.user.full_name} ({x.staff_id})") for x in r.siso_profiles()];form.school_id.choices=[(str(x.id),f"{x.school_name} ({x.school_code})") for x in r.schools()];form.academic_year_id.choices=[(str(x.id),x.name) for x in r.years()]
 if form.validate_on_submit():
  try:r.assign_siso(form.siso_id.data,form.school_id.data,form.academic_year_id.data);log_action(current_user.id,"ASSIGN_SISO_SCHOOL","school_supervision_assignment");flash("School assigned to SISO.","success")
  except Exception as e:fail(e)
 return render_template("admin/siso_assignments.html",form=form,assignments=r.siso_assignments())
@admin_bp.route("/classes",methods=["GET","POST"])
@login_required
@require_role("ADMIN")
def classes():
 r=repo();form=ClassForm()
 if form.validate_on_submit():
  try:r.add_class(form.name.data);log_action(current_user.id,"CREATE_CLASS","Class");flash("Class added.","success")
  except Exception as e:fail(e)
 return render_template("admin/classes.html",form=form,classes=r.classes())
@admin_bp.route("/subjects",methods=["GET","POST"])
@login_required
@require_role("ADMIN")
def subjects():
 r=repo();form=SubjectForm()
 if form.validate_on_submit():
  try:r.add_subject(form.name.data);log_action(current_user.id,"CREATE_SUBJECT","Subject");flash("Subject added.","success")
  except Exception as e:fail(e)
 return render_template("admin/subjects.html",form=form,subjects=r.subjects())
@admin_bp.route("/academic-years",methods=["GET","POST"])
@login_required
@require_role("ADMIN")
def academic_years():
 r=repo();form=AcademicYearForm()
 if form.validate_on_submit():
  try:r.add_year(form.label.data);log_action(current_user.id,"CREATE_ACADEMIC_YEAR","AcademicYear");flash("Academic year added.","success")
  except Exception as e:fail(e)
 years=r.years()
 for y in years:y.label=y.name
 return render_template("admin/academic_years.html",form=form,years=years)
@admin_bp.route("/terms",methods=["GET","POST"])
@login_required
@require_role("ADMIN")
def terms():
 r=repo();form=TermForm();form.academic_year_id.choices=[(str(y.id),y.name) for y in r.years()]
 if form.validate_on_submit():
  try:r.add_term(form.academic_year_id.data,form.name.data);log_action(current_user.id,"CREATE_TERM","Term");flash("Term added.","success")
  except Exception as e:fail(e)
 return render_template("admin/terms.html",form=form,terms=r.terms())
@admin_bp.route("/deadlines",methods=["GET","POST"])
@login_required
@require_role("ADMIN")
def deadlines():
 r=repo();form=DeadlineForm();form.term_id.choices=[(str(t.id),f"{t.label} — {t.name}") for t in r.terms()]
 if form.validate_on_submit():
  try:r.add_deadline(form.term_id.data,form.week.data,form.due_at.data);log_action(current_user.id,"CREATE_DEADLINE","Deadline");flash("Deadline added.","success")
  except Exception as e:fail(e)
 return render_template("admin/deadlines.html",form=form,deadlines=r.deadlines())
@admin_bp.route("/teacher-assignments",methods=["GET","POST"])
@login_required
@require_role("ADMIN")
def teacher_assignments():
 r=repo();form=TeacherAssignmentForm();profiles=r.client.table("teacher_profiles").select("id,user_id,staff_id,users(first_name,last_name)").eq("is_active",True).execute().data or [];form.teacher_id.choices=[(str(x["id"]),f"{(x.get('users') or {}).get('first_name','')} {(x.get('users') or {}).get('last_name','')}") for x in profiles];form.subject_id.choices=[(str(x.id),x.name) for x in r.subjects()];form.class_id.choices=[(str(x.id),x.name) for x in r.classes()];form.academic_year_id.choices=[(str(x.id),x.name) for x in r.years()];form.term_id.choices=[("","All terms")]+[(str(x.id),f"{x.label} — {x.name}") for x in r.terms()]
 if form.validate_on_submit():
  try:r.add_assignment(form.teacher_id.data,form.subject_id.data,form.class_id.data,form.academic_year_id.data,form.term_id.data or None);log_action(current_user.id,"CREATE_TEACHER_ASSIGNMENT","TeacherAssignment");flash("Assignment created.","success")
  except Exception as e:fail(e)
 return render_template("admin/teacher_assignments.html",form=form,assignments=r.assignments())
@admin_bp.route("/settings",methods=["GET","POST"])
@login_required
@require_role("ADMIN")
def settings():
 r=repo();form=WorkflowSettingsForm();years=r.years();terms=r.terms();s=r.settings() or {};form.current_academic_year_id.choices=[("","— none —")]+[(str(y.id),y.name) for y in years];form.current_term_id.choices=[("","— none —")]+[(str(t.id),f"{t.label} — {t.name}") for t in terms]
 if request.method=="GET":form.current_academic_year_id.data=str(s.get("current_academic_year_id") or "");form.current_term_id.data=str(s.get("current_term_id") or "")
 if form.validate_on_submit():
  try:r.update_settings(form.current_academic_year_id.data,form.current_term_id.data);log_action(current_user.id,"UPDATE_SYSTEM_SETTINGS","SystemSettings");flash("Settings saved.","success");return redirect(url_for("admin.settings"))
  except Exception as e:fail(e)
 return render_template("admin/settings.html",form=form)
@admin_bp.route("/audit-logs")
@login_required
@require_role("ADMIN")
def audit_logs():action=request.args.get("action");return render_template("admin/audit_logs.html",logs=repo().audit_logs(action),action_filter=action)
