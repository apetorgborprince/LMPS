from flask import Blueprint,render_template,redirect,url_for,request
from flask_login import login_required,current_user
from app.data_supabase import _client,_rows
from types import SimpleNamespace
notifications_bp=Blueprint("notifications",__name__,url_prefix="/notifications",template_folder="../../templates/notifications")
def unread_count(user):
 try:return len(_rows(_client().table("notifications").select("id").eq("recipient_user_id",str(user.id)).eq("is_read",False).execute()))
 except Exception:return 0
@notifications_bp.route("/")
@login_required
def list_notifications():
 rows=_rows(_client().table("notifications").select("id,recipient_user_id,notification_type,title,message,entity_type,entity_id,is_read,read_at,created_at").eq("recipient_user_id",str(current_user.id)).order("created_at",desc=True).limit(100).execute());return render_template("notifications/list.html",notifications=[SimpleNamespace(**r) for r in rows])
@notifications_bp.route("/<notification_id>/read",methods=["POST"])
@login_required
def mark_read(notification_id):
 _client().table("notifications").update({"is_read":True}).eq("id",str(notification_id)).eq("recipient_user_id",str(current_user.id)).execute();return redirect(request.args.get("next") or url_for("notifications.list_notifications"))
@notifications_bp.route("/mark-all-read",methods=["POST"])
@login_required
def mark_all_read():
 _client().table("notifications").update({"is_read":True}).eq("recipient_user_id",str(current_user.id)).eq("is_read",False).execute();return redirect(url_for("notifications.list_notifications"))
