import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    """Base configuration. All secrets come from environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY environment variable is not set. Copy .env.example to .env and configure it.")

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    UPLOAD_STORAGE_PATH = os.environ.get("UPLOAD_STORAGE_PATH", "./storage")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_SIZE_MB", 10)) * 1024 * 1024
    ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "doc", "docx"}
    ALLOWED_UPLOAD_MIME_TYPES = {"application/pdf","application/msword","application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    SESSION_TOKEN_DIR = os.environ.get("SESSION_TOKEN_DIR", os.path.join(basedir, ".session_tokens"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES", 60)))
    WTF_CSRF_ENABLED = True
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
    MAIL_ENABLED = bool(MAIL_SERVER)


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {"development": DevelopmentConfig, "production": ProductionConfig}
