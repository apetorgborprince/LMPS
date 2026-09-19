from flask import Blueprint,abort,send_file
from flask_login import login_required,current_user
from app.data_supabase import _client,_first
from app.utils.audit import log_action
import io
files_bp=Blueprint("files",__name__)
@files_bp.route("/files/<attachment_id>")
@login_required
def download(attachment_id):
 row=_first(_client().table("plan_attachments").select("id,file_name,storage_path,mime_type,file_size_bytes,learner_plan_id").eq("id",str(attachment_id)).maybe_single().execute())
 if not row:abort(404)
 plan=_first(_client().table("learner_plans").select("id,status").eq("id",str(row["learner_plan_id"])).maybe_single().execute())
 if not plan:abort(404)
 if current_user.role_name not in ("ADMIN","HEADMASTER") and plan.get("status")!="APPROVED":abort(403)
 try:data=_client().storage.from_("learner-plan-attachments").download(row["storage_path"])
 except Exception:abort(404)
 log_action(current_user.id,"DOWNLOAD","plan_attachment",row["id"]);return send_file(io.BytesIO(data),download_name=row["file_name"],as_attachment=True,mimetype=row.get("mime_type") or "application/octet-stream")
