from flask import request
from app.supabase_client import client_for_access_token
from app.supabase_auth import current_access_token

def log_action(user_id,action,entity_type=None,entity_id=None,result="SUCCESS"):
 token=current_access_token()
 if not token:return None
 payload={"actor_user_id":str(user_id) if user_id else None,"action":action,"entity_type":entity_type,"entity_id":str(entity_id) if entity_id else None,"ip_address":request.remote_addr if request else None,"user_agent":request.headers.get("User-Agent") if request else None,"new_data":{"result":result}}
 try:return client_for_access_token(token).table("audit_logs").insert(payload).execute()
 except Exception:return None
