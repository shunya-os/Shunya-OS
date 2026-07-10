"""
Celery worker config for async tasks like PDF generation.
Requires REDIS_URL/CELERY_BROKER_URL env var.
"""
from celery import Celery
import os
celery = Celery('panchi', broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'), backend=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
celery.conf.task_serializer = 'json'
celery.conf.result_serializer = 'json'
celery.conf.accept_content = ['json']
celery.conf.task_track_started = True

@celery.task()
def generate_invoice_pdf(invoice_id: int, path: str):
    from app.services import _generate_invoice_pdf
    _generate_invoice_pdf(invoice_id, path)
