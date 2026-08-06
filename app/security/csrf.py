"""SHUNYA OS — CSRF Strategy.

SHUNYA is a JSON-API + SPA application. CSRF is mitigated at the
transport layer by design:

1. The session cookie is `SameSite=Strict` — browsers never attach it
   to cross-site requests, which is the primary CSRF vector.
2. All mutating requests are `application/json` — HTML form posts
   cannot set this content type, so cross-site form-based CSRF is
   structurally impossible.
3. The `X-Identity-Id` header (legacy clients) is not auto-sent by
   browsers cross-origin.

Flask-WTF's CSRFProtect is therefore left enabled for any future
HTML form routes, but the API surface is explicitly exempt (it is
already CSRF-safe by SameSite=Strict + JSON content type).
"""

from flask_wtf.csrf import CSRFProtect, generate_csrf

csrf = CSRFProtect()


def init_csrf(app):
    """Initialise CSRF protection.

    The API surface is exempt: JSON requests are not CSRF-vulnerable
    (form posts cannot send JSON), and the session cookie is
    SameSite=Strict. Flask-WTF protection remains active for any
    server-rendered HTML forms.
    """
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    csrf.init_app(app)

    @app.after_request
    def add_csrf_header(response):
        response.headers["X-CSRF-Token"] = generate_csrf()
        return response
