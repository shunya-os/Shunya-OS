"""
Optional monitoring setup without touching app/__init__.py core factory.
Call init_monitoring(app) after create_app() when SENTRY_DSN is set.
"""
import os
from flask import request, g

def init_monitoring(app):
    dsn = os.getenv('SENTRY_DSN')
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(dsn=dsn, integrations=[FlaskIntegration()], traces_sample_rate=0.0)
        @app.before_request
        def _sentry_context():
            sentry_sdk.set_user({'id': str(request.headers.get('X-Telegram-Chat-Id') or request.remote_addr)})
            g.request_id = getattr(g, 'request_id', '')
            sentry_sdk.set_tag('request_id', g.request_id)
    except Exception as e:
        app.logger.warning('Sentry init failed: %s', e)
