"""WSGI entrypoint for production servers (gunicorn)."""

from app import create_app

app = create_app()
