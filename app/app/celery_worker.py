"""
Legacy Celery worker entry point.
Routes to app.cache which has the consolidated Celery + cache logic.
"""
# Re-export tasks for `celery -A app.celery_worker worker` compatibility
from app.cache import get_celery
celery = get_celery()
app = celery  # provides `celery_app` for CLI: celery -A app.celery_worker worker