import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from app.config import config_by_name
from app.extensions import db, login_manager, csrf, migrate, limiter


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "production")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    if config_name == "production":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        if config_name == "production":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    from app.supabase_auth import load_current_user
    @login_manager.user_loader
    def load_user(user_id):
        return load_current_user(user_id)

    from app.blueprints.auth import auth_bp
    from app.blueprints.teacher import teacher_bp
    from app.blueprints.files import files_bp
    from app.blueprints.headmaster import headmaster_bp
    from app.blueprints.siso import siso_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(headmaster_bp)
    app.register_blueprint(siso_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)

    from flask_login import current_user
    from app.blueprints.notifications.routes import unread_count

    @app.template_filter("pill_class")
    def pill_class(status):
        return str(status).lower().replace("_", "-")

    @app.context_processor
    def inject_unread_notifications():
        return {"unread_notification_count": unread_count(current_user) if current_user.is_authenticated else 0}

    from flask import render_template
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("shared/error.html", code=403, message="You don't have permission to view that page."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("shared/error.html", code=404, message="That page could not be found."), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        return render_template("shared/error.html", code=500, message="Something went wrong on our end. Please try again, or contact your administrator."), 500

    return app
