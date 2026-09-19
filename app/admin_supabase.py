"""Server-side Supabase administration repository."""
import secrets,string
from app.supabase_client import get_service_client,client_for_access_token
from app.data_supabase import _rows,_first,_obj,SupabaseDataError
class AdminRepository:
 def __init__(self):
  from app.supabase_auth import current_access_token
  token=current_access_token()
  if not token: raise SupabaseDataError("Your session has expired. Please sign in again.")
  self.client=client_for_access_token(token); self.service=get_service_client()
 def users(self):
  rows=_rows(self.client.table("users").select("id,auth_user_id,email,first_name,last_name,phone,is_active,roles(name)").order("last_name").execute()); out=[]
  for r in rows:
   role=r.pop("roles",None) or {}; r["role"]=_obj(role); r["full_name"]=f"{r.get('first_name','')} {r.get('last_name','')}".strip(); r["is_active_user"]=r.get("is_active"); out.append(_obj(r))
  return out
 def counts(self): return {"users":len(self.users()),"teachers":len(_rows(self.client.table("teacher_profiles").select("id").eq("is_active",True).execute())),"classes":len(_rows(self.client.table("classes").select("id").eq("is_active",True).execute())),"subjects":len(_rows(self.client.table("subjects").select("id").eq("is_active",True).execute()))}
 def create_user(self,email,full_name,role_name,phone=None,staff_id=None):
  parts=full_name.strip().split(maxsplit=1); first=parts[0]; last=parts[1] if len(parts)>1 else ""; password=secrets.token_urlsafe(9)+"A1!"
  auth=self.service.auth.admin.create_user({"email":email,"password":password,"email_confirm":True}); au=getattr(auth,"user",None)
  if not au: raise SupabaseDataError("Supabase Auth did not create the user.")
  role=_first(self.client.table("roles").select("id,name").eq("name",role_name).maybe_single().execute())
  if not role: raise SupabaseDataError("Invalid role.")
  row=_first(self.service.table("users").insert({"auth_user_id":au.id,"email":email,"first_name":first,"last_name":last,"phone":phone,"role_id":role["id"],"is_active":True}).select("id").single().execute())
  profile={"user_id":row["id"],"staff_id":staff_id or email.split("@")[0],"is_active":True}
  if role_name=="TEACHER":self.service.table("teacher_profiles").insert(profile).execute()
  elif role_name=="HEADMASTER":self.service.table("headmaster_profiles").insert({**profile,"appointment_date":None}).execute()
  elif role_name=="SISO":self.service.table("siso_profiles").insert({**profile,"circuit":None,"district":None}).execute()
  return self._get(row["id"]),password
 def _get(self,user_id):
  row=_first(self.service.table("users").select("id,auth_user_id,email,first_name,last_name,phone,is_active,roles(name)").eq("id",str(user_id)).maybe_single().execute())
  if not row:return None
  role=row.pop("roles",None) or {}; row["role"]=_obj(role); row["full_name"]=f"{row.get('first_name','')} {row.get('last_name','')}".strip(); row["is_active_user"]=row.get("is_active"); return _obj(row)
 def set_active(self,user_id,active):
  row=_first(self.service.table("users").select("auth_user_id").eq("id",str(user_id)).maybe_single().execute())
  if not row:raise SupabaseDataError("User not found.")
  self.service.table("users").update({"is_active":bool(active)}).eq("id",str(user_id)).execute(); return self._get(user_id)
 def reset_password(self,user_id):
  row=_first(self.service.table("users").select("auth_user_id,email").eq("id",str(user_id)).maybe_single().execute())
  if not row:raise SupabaseDataError("User not found.")
  alphabet=string.ascii_letters+string.digits+"!@#$%"; password="".join(secrets.choice(alphabet) for _ in range(14))+"A1!"; self.service.auth.admin.update_user_by_id(row["auth_user_id"],{"password":password}); return password
 def schools(self):return [_obj(x) for x in _rows(self.client.table("schools").select("id,school_name,school_code,circuit,district,is_active").order("school_name").execute())]
 def siso_profiles(self):
  rows=_rows(self.client.table("siso_profiles").select("id,user_id,staff_id,circuit,district,is_active,users(first_name,last_name,email)").eq("is_active",True).order("staff_id").execute())
  for r in rows:u=r.pop("users",None) or {};r["user"]=_obj({**u,"full_name":f"{u.get('first_name','')} {u.get('last_name','')}".strip()})
  return [_obj(r) for r in rows]
 def siso_assignments(self):
  rows=_rows(self.client.table("school_supervision_assignments").select("id,siso_id,school_id,academic_year_id,school_name,school_code,assigned_date,is_active,siso_profiles(staff_id,users(first_name,last_name)),academic_years(name)").order("assigned_date",desc=True).execute()); out=[]
  for r in rows:
   sp=r.pop("siso_profiles",None) or {};u=sp.get("users") or {};r["siso"]=_obj({"staff_id":sp.get("staff_id"),"user":_obj({"full_name":f"{u.get('first_name','')} {u.get('last_name','')}".strip()})});r["academic_year"]=_obj(r.pop("academic_years",None));out.append(_obj(r))
  return out
 def add_school(self,name,code,circuit=None,district=None):return self.client.table("schools").insert({"school_name":name,"school_code":code,"circuit":circuit,"district":district,"is_active":True}).execute()
 def assign_siso(self,siso_id,school_id,year_id):
  school=_first(self.client.table("schools").select("school_name,school_code").eq("id",str(school_id)).maybe_single().execute()); return self.client.table("school_supervision_assignments").insert({"siso_id":str(siso_id),"school_id":str(school_id),"academic_year_id":str(year_id),"school_name":school["school_name"],"school_code":school["school_code"],"is_active":True}).execute()
 def classes(self):return [_obj(x) for x in _rows(self.client.table("classes").select("id,name,level,description,is_active").order("name").execute())]
 def subjects(self):return [_obj(x) for x in _rows(self.client.table("subjects").select("id,code,name,description,is_active").order("name").execute())]
 def years(self):return [_obj(x) for x in _rows(self.client.table("academic_years").select("id,name,start_date,end_date,is_current").order("name",desc=True).execute())]
 def terms(self):
  rows=_rows(self.client.table("terms").select("id,academic_year_id,name,term_number,start_date,end_date,is_current,academic_years(name)").order("term_number").execute())
  for r in rows:r["academic_year"]=_obj(r.pop("academic_years",None));r["label"]=getattr(r["academic_year"],"name","")
  return [_obj(r) for r in rows]
 def deadlines(self):
  rows=_rows(self.client.table("deadlines").select("id,term_id,week,due_at,terms(name,academic_years(name))").order("due_at").execute())
  for r in rows:t=r.pop("terms",None) or {};r["term"]=_obj({"name":t.get("name"),"academic_year":_obj(t.get("academic_years") or {})})
  return [_obj(r) for r in rows]
 def add_class(self,name):return self.client.table("classes").insert({"name":name}).execute()
 def add_subject(self,name):return self.client.table("subjects").insert({"name":name,"code":name.upper().replace(" ","_")[:20]}).execute()
 def add_year(self,label):return self.client.table("academic_years").insert({"name":label}).execute()
 def add_term(self,year_id,name):
  existing=_rows(self.client.table("terms").select("term_number").eq("academic_year_id",str(year_id)).execute());n=max([x.get("term_number") or 0 for x in existing] or [0])+1;return self.client.table("terms").insert({"academic_year_id":str(year_id),"name":name,"term_number":n}).execute()
 def add_deadline(self,term_id,week,due_at):return self.client.table("deadlines").insert({"term_id":str(term_id),"week":int(week),"due_at":due_at.isoformat()}).execute()
 def assignments(self):
  rows=_rows(self.client.table("teacher_assignments").select("id,teacher_id,subject_id,class_id,academic_year_id,term_id,teacher_profiles(staff_id,users(first_name,last_name)),subjects(name),classes(name),academic_years(name),terms(name)").order("id").execute());out=[]
  for r in rows:
   tp=r.pop("teacher_profiles",{}) or {};u=tp.get("users") or {};r["teacher"]=_obj({"user":_obj({"full_name":f"{u.get('first_name','')} {u.get('last_name','')}".strip()}),"staff_id":tp.get("staff_id")});r["subject"]=_obj(r.pop("subjects",None));r["class_"]=_obj(r.pop("classes",None));out.append(_obj(r))
  return out
 def add_assignment(self,teacher_id,subject_id,class_id,year_id,term_id=None):return self.client.table("teacher_assignments").insert({"teacher_id":str(teacher_id),"subject_id":str(subject_id),"class_id":str(class_id),"academic_year_id":str(year_id),"term_id":str(term_id) if term_id else None}).execute()
 def settings(self):return _first(self.client.table("system_settings").select("id,school_name,school_code,current_academic_year_id,current_term_id,schools(id,school_name,school_code)").limit(1).execute())
 def update_settings(self,year_id,term_id):
  s=self.settings();payload={"current_academic_year_id":str(year_id) if year_id else None,"current_term_id":str(term_id) if term_id else None};return self.client.table("system_settings").update(payload).eq("id",s["id"]).execute() if s else self.client.table("system_settings").insert(payload).execute()
 def audit_logs(self,action=None):
  q=self.client.table("audit_logs").select("id,actor_user_id,action,entity_type,entity_id,new_data,created_at,users(first_name,last_name,email)").order("created_at",desc=True).limit(200)
  if action:q=q.eq("action",action)
  rows=_rows(q.execute())
  for r in rows:u=r.pop("users",None) or {};r["user"]=_obj({"full_name":f"{u.get('first_name','')} {u.get('last_name','')}".strip()});r["result"]=(r.get("new_data") or {}).get("result","SUCCESS")
  return [_obj(r) for r in rows]
