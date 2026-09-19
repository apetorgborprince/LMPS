import csv,io
from flask import Blueprint,render_template,abort,Response,request,redirect,url_for,flash
from flask_login import login_required,current_user
from app.utils.decorators import require_role
from app.utils.audit import log_action
from app.services import pdf_service
from app.siso_supabase import SISORepository
siso_bp=Blueprint("siso",__name__,url_prefix="/siso",template_folder="../../templates/siso")
def repo():return SISORepository()
def _current_year_term():
 from app.admin_supabase import AdminRepository
 r=AdminRepository();s=r.settings() or {};years={str(y.id):y for y in r.years()};terms={str(t.id):t for t in r.terms()};return years.get(str(s.get("current_academic_year_id"))),terms.get(str(s.get("current_term_id")))
@siso_bp.route("/dashboard")
@login_required
@require_role("SISO")
def dashboard():y,t=_current_year_term();return render_template("siso/dashboard.html",stats=repo().dashboard(),year=y,term=t)
@siso_bp.route("/teachers")
@login_required
@require_role("SISO")
def teachers():return render_template("siso/teachers.html",teachers=repo().teachers())
@siso_bp.route("/teachers/<teacher_id>")
@login_required
@require_role("SISO")
def teacher_detail(teacher_id):
 teacher=next((t for t in repo().teachers() if str(t.id)==str(teacher_id)),None)
 if not teacher:abort(404)
 return render_template("siso/teacher_detail.html",teacher=teacher,plans=repo().teacher_plans(teacher_id))
@siso_bp.route("/plans/<plan_id>")
@login_required
@require_role("SISO")
def plan_detail(plan_id):
 plan=repo().plan_detail(plan_id)
 if not plan:abort(404)
 log_action(current_user.id,"SISO_VIEW_PLAN","learner_plan",plan.id);return render_template("siso/plan_detail.html",plan=plan)
@siso_bp.route("/visits")
@login_required
@require_role("SISO")
def visits():return render_template("siso/visits.html",visits=repo().visits())
@siso_bp.route("/visits/new",methods=["GET","POST"])
@login_required
@require_role("SISO")
def new_visit():
 schools=repo().assigned_schools()
 if request.method=="POST":
  try:
   row=repo().create_visit(request.form.get("school_assignment_id"),request.form.get("visit_date"),request.form.get("visit_type"),request.form.get("purpose"),request.form.get("general_observation"));log_action(current_user.id,"CREATE_SISO_VISIT","siso_monitoring_visit",row.get("id"));flash("Monitoring visit recorded.","success");return redirect(url_for("siso.visits"))
  except Exception as e:flash(str(e),"error")
 return render_template("siso/new_visit.html",schools=schools)
def _reports():return repo().reports()
@siso_bp.route("/reports/teacher-compliance")
@login_required
@require_role("SISO")
def report_teacher_compliance():
 rows,_,_=_reports();rows=list(rows);fmt=request.args.get("format")
 if fmt=="csv":return _csv_response(rows,["teacher","staff_id","expected","submitted","approved","pending","compliance_pct"],"teacher_compliance_report.csv")
 if fmt=="pdf":return _pdf_response("Teacher Compliance Report",["Teacher","Staff ID","Expected","Submitted","Approved","Pending","Compliance %"],[[r["teacher"],r["staff_id"],r["expected"],r["submitted"],r["approved"],r["pending"],f"{r['compliance_pct']}%"] for r in rows],"teacher_compliance_report.pdf")
 y,t=_current_year_term();return render_template("siso/report_teacher_compliance.html",rows=rows,year=y,term=t)
@siso_bp.route("/reports/plan-status")
@login_required
@require_role("SISO")
def report_plan_status():
 _,rows,_=_reports();fmt=request.args.get("format")
 if fmt=="csv":return _csv_response(rows,["reference","teacher","subject","class","week","status"],"plan_status_report.csv")
 if fmt=="pdf":return _pdf_response("Learner Plan Status Report",["Reference","Teacher","Subject","Class","Week","Status"],[[r["reference"],r["teacher"],r["subject"],r["class"],r["week"],r["status"]] for r in rows],"plan_status_report.pdf")
 y,t=_current_year_term();return render_template("siso/report_plan_status.html",rows=rows,year=y,term=t)
@siso_bp.route("/reports/school-monitoring")
@login_required
@require_role("SISO")
def report_school_monitoring():
 _,_,row=_reports();fmt=request.args.get("format")
 if fmt=="csv":return _csv_response([row],["school","teachers","expected","submitted","approved","pending"],"school_monitoring_report.csv")
 if fmt=="pdf":return _pdf_response("School Monitoring Report",["School","Teachers","Expected","Submitted","Approved","Pending"],[[row["school"],row["teachers"],row["expected"],row["submitted"],row["approved"],row["pending"]]],"school_monitoring_report.pdf")
 y,t=_current_year_term();return render_template("siso/report_school_monitoring.html",row=row,year=y,term=t)
def _csv_response(rows,fields,filename):
 b=io.StringIO();w=csv.DictWriter(b,fieldnames=fields);w.writeheader();[w.writerow(r) for r in rows];log_action(current_user.id,"EXPORT_REPORT_CSV","Report");return Response(b.getvalue(),mimetype="text/csv",headers={"Content-Disposition":f"attachment; filename={filename}"})
def _pdf_response(title,headers,rows,filename):
 y,t=_current_year_term();data=pdf_service.build_report_pdf(title=title,generated_by=current_user.full_name,academic_year_label=getattr(y,"name",None),term_name=getattr(t,"name",None),headers=headers,rows=rows);log_action(current_user.id,"EXPORT_REPORT_PDF","Report");return Response(data,mimetype="application/pdf",headers={"Content-Disposition":f"attachment; filename={filename}"})
