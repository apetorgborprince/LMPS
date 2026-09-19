"""Vercel entrypoint for the LMPS Flask application.

Vercel's Python runtime imports the WSGI application from this module.
Keep secrets in Vercel Environment Variables; never commit them here.
"""
from wsgi import app

__all__ = ["app"]
