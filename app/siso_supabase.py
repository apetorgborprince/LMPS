"""Supabase repository for SISO monitoring and reporting."""
from app.data_supabase import _client,_rows,_first,_obj
class SISORepository:
 def __init__(self):self.client=_client()
 def profile(self):
  from flask_login import current_user
  return _obj(_first(self.client.table("siso_profiles").select("id,user_id,staff_id,circuit,district,appointment_date,is_active").eq("user_id",str(current_user.id)).eq("is_active",True).maybe_single().execute()))
 def assigned_schools(self):return [_obj(x) for x in _rows(self.client.table("siso_assigned_schools").select("*").execute())]
 def dashboard(self):
  rows=_rows(self.client.table("siso_monitoring_summary").select("*").execute()); summary={"schools":len(rows),"visits":sum(int(r.get("total_visits") or 0) for r in rows),"open_actions":sum(int(r.get("open_action_points") or 0) for r in rows),"completed_actions":sum(int(r.get("completed_action_points") or 0) for r in rows),"follow_ups_required":sum(int(r.get("visits_requiring_follow_up") or 0) for r in rows)};summary["assigned_schools"]=self.assigned_schools();return summary
 def teachers(self):
  rows=_rows(self.client.table("teacher_profiles").select("id,user_id,staff_id,employee_number,is_active,users(id,first_name,last_name,email)").eq("is_active",True).order("staff_id").execute());out=[]
  for r in rows:u=r.pop("users",None) or {};r["user"]=_obj({**u,"full_name":f"{u.get('first_name','')} {u.get('last_name','')}".strip()});out.append(_obj(r))
  return out
 def teacher_plans(self,teacher_id):
  rows=_rows(self.client.table("learner_plans").select("id,reference,week_number,status,current_version_id,academic_year_id,term_id,classes(id,name),subjects(id,name),teacher_assignments!inner(id,teacher_id,teacher_profiles!inner(id,staff_id))").eq("teacher_assignments.teacher_id",str(teacher_id)).eq("status","APPROVED").order("week_number").execute());out=[]
  for r in rows:r["class_"]=_obj(r.pop("classes",None));r["subject"]=_obj(r.pop("subjects",None));r["week"]=r.pop("week_number");ta=r.pop("teacher_assignments",None) or {};r["teacher_id"]=ta.get("teacher_id");r["current_status"]=r.pop("status");out.append(_obj(r))
  return out
 def plan_detail(self,plan_id):
  row=_first(self.client.table("siso_approved_learner_plans").select("*").eq("id",str(plan_id)).maybe_single().execute());
  if not row:return None
  p=dict(row);p["class_"]=_obj({"name":p.get("class_name")});p["subject"]=_obj({"name":p.get("subject_name")});p["week"]=p.get("week_number");p["current_status"]="APPROVED";p["teacher_id"]=p.get("teacher_assignment_id");vs=_rows(self.client.table("learner_plan_versions").select("id,version_number,content,created_at,created_by").eq("learner_plan_id",str(plan_id)).order("version_number").execute());p["versions"]=[_obj({**v,**(v.get("content") or {})}) for v in vs];p["current_version"]=next((v for v in p["versions"] if str(v.id)==str(p.get("current_version_id"))),p["versions"][-1] if p["versions"] else None);return _obj(p)
 def visits(self,limit=100):
  rows=_rows(self.client.table("siso_monitoring_visits").select("id,supervision_assignment_id,visit_date,visit_type,purpose,general_observation,overall_status,created_at,school_supervision_assignments(school_name,school_code)").order("visit_date",desc=True).limit(limit).execute())
  for r in rows:r["school"]=_obj(r.pop("school_supervision_assignments",None))
  return [_obj(r) for r in rows]
 def create_visit(self,school_assignment_id,visit_date,visit_type,purpose,observation):
  from flask_login import current_user
  return _first(self.client.table("siso_monitoring_visits").insert({"supervision_assignment_id":str(school_assignment_id),"visit_date":visit_date,"visit_type":visit_type,"purpose":purpose,"general_observation":observation,"created_by":str(current_user.id)}).select("id").single().execute())
 def reports(self):
  approved=_rows(self.client.table("siso_approved_learner_plans").select("id,reference,subject_name,class_name,week_number,status,academic_year_id,term_id,teacher_assignment_id,teacher_assignments(teacher_profiles(staff_id,users(first_name,last_name)))").execute());teachers={}
  for p in approved:
   ta=p.get("teacher_assignments") or {};tp=ta.get("teacher_profiles") or {};u=tp.get("users") or {};staff_id=tp.get("staff_id");name=f"{u.get('first_name','')} {u.get('last_name','')}".strip();key=staff_id or name;t=teachers.setdefault(key,{"teacher":name,"staff_id":staff_id,"submitted":0,"approved":0,"pending":0});t["approved"]+=1;t["submitted"]+=1
  for t in teachers.values():t["expected"]=t["approved"];t["pending"]=0;t["compliance_pct"]=100 if t["expected"] else 0
  plans=_rows(self.client.table("learner_plans").select("id,reference,week_number,status,teacher_assignments!inner(teacher_profiles!inner(staff_id,users(first_name,last_name)),subjects(name),classes(name))").execute());status=[]
  for p in plans:
   ta=p.get("teacher_assignments") or {};tp=ta.get("teacher_profiles") or {};u=tp.get("users") or {};status.append({"reference":p.get("reference"),"teacher":f"{u.get('first_name','')} {u.get('last_name','')}".strip(),"subject":(ta.get("subjects") or {}).get("name"),"class":(ta.get("classes") or {}).get("name"),"week":p.get("week_number"),"status":p.get("status")})
  schools=self.assigned_schools();school=schools[0] if schools else None;monitoring={"school":getattr(school,"school_name",None) if school else None,"teachers":len(self.teachers()),"expected":len(approved),"submitted":len(approved),"approved":len(approved),"pending":0};return teachers.values(),status,monitoring
