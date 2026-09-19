from flask import Blueprint,render_template,redirect,url_for,flash
from flask_login import login_required,current_user,logout_user
from app.extensions import limiter
from app.supabase_auth import sign_in,sign_out
from app.supabase_client import get_public_client
from app.utils.audit import log_action
from app.blueprints.auth.forms import LoginForm,ForgotPasswordForm,ResetPasswordForm
auth_bp=Blueprint("auth",__name__,template_folder="../../templates/auth")
@auth_bp.route("/login",methods=["GET","POST"])
@limiter.limit("10 per minute")
def login():
 if current_user.is_authenticated:return redirect(url_for("auth.post_login_redirect"))
 form=LoginForm()
 if form.validate_on_submit():
  try:user=sign_in(form.email.data.lower().strip(),form.password.data)
  except Exception:user=None
  if user is None:flash("Invalid email or password.","error");return render_template("auth/login.html",form=form)
  log_action(user.id,"LOGIN","User",user.id);return redirect(url_for("auth.post_login_redirect"))
 return render_template("auth/login.html",form=form)
@auth_bp.route("/post-login-redirect")
@login_required
def post_login_redirect():
 endpoint={"ADMIN":"admin.dashboard","TEACHER":"teacher.dashboard","HEADMASTER":"headmaster.dashboard","SISO":"siso.dashboard"}.get(current_user.role_name)
 return redirect(url_for(endpoint)) if endpoint else redirect(url_for("auth.login"))
@auth_bp.route("/logout")
@login_required
def logout():
 user_id=current_user.id;log_action(user_id,"LOGOUT","User",user_id)
 try:sign_out()
 finally:logout_user()
 flash("You have been logged out.","info");return redirect(url_for("auth.login"))
@auth_bp.route("/forgot-password",methods=["GET","POST"])
@limiter.limit("5 per minute")
def forgot_password():
 form=ForgotPasswordForm()
 if form.validate_on_submit():
  try:get_public_client().auth.reset_password_email(form.email.data.lower().strip())
  except Exception:pass
  flash("If an account exists for that email, a password reset link has been sent.","info");return redirect(url_for("auth.login"))
 return render_template("auth/forgot_password.html",form=form)
@auth_bp.route("/reset-password/<token>",methods=["GET","POST"])
def reset_password(token):
 flash("Password reset is handled by Supabase Auth. Use the link sent to your email.","info");return redirect(url_for("auth.login"))
