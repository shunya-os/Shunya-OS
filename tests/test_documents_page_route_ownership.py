"""Documents PAGE route ownership — the /documents page-route collision guard.

Three registrations once overlapped on the `main` blueprint:

  * main.documents_page      — GET /documents          → SPA shell (release-aware).
        CANONICAL owner for the document collection page.
  * main.documents_detail    — GET /documents/<int:id> → rendered the never-created
        template "documents.html"; every real document id crashed with
        TemplateNotFound (HTTP 500) in production.
  * main._legacy_spa_fallback — GET /documents + GET /documents/<int:id> (among
        other legacy paths) → served the raw checkout dist tree (non-release-aware).

With duplicate rules the handler is decided by registration order — and one of the
candidates crashed. The intended contract: exactly one owner per page rule, and both
/documents and /documents/<id> serve the SPA shell so client-side routing owns the
deep links, exactly like every other SPA path (/living).

The de-duplication must NOT drop the fallback's other legacy paths (/leads,
/invoices, ...) nor the /documents/upload POST route.
"""

import os

# Ensure the SPA shell exists so shell-serving routes can return 200.
# In CI the frontend is built in a LATER step than the Python tests; a mock
# shell keeps the contract testable. Never overwrites a real build.
dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
os.makedirs(dist_dir, exist_ok=True)
_shell_path = os.path.join(dist_dir, "index.html")
if not os.path.exists(_shell_path):
    with open(_shell_path, "w") as _f:
        _f.write('<!doctype html><html><body data-test-shell>SHUNYA</body></html>')


def _app():
    from app import create_app
    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })


def _owners(app):
    owners = {}
    for rule in app.url_map.iter_rules():
        for method in (rule.methods - {"HEAD", "OPTIONS"}):
            owners.setdefault((str(rule), method), []).append(rule.endpoint)
    return owners


def _documents_page_collisions(app):
    """Duplicate owners for any /documents* page rule."""
    return {
        key: eps for key, eps in _owners(app).items()
        if len(eps) > 1 and key[0].startswith("/documents")
    }


def test_no_duplicate_documents_page_rules():
    """No page rule under /documents may have two owners."""
    collisions = _documents_page_collisions(_app())
    assert collisions == {}, f"ambiguous page-route precedence: {collisions}"


def test_documents_page_owner_is_the_spa_shell_route():
    """GET /documents is owned by the canonical SPA shell route."""
    endpoint, _ = _app().url_map.bind("localhost").match("/documents", method="GET")
    assert endpoint == "main.documents_page", (
        f"GET /documents is owned by {endpoint!r}; the canonical documents_page "
        "route must own it"
    )


def test_documents_detail_owner_is_explicit():
    """GET /documents/<id> is owned by the documents detail route."""
    endpoint, _ = _app().url_map.bind("localhost").match("/documents/42", method="GET")
    assert endpoint == "main.documents_detail", (
        f"GET /documents/42 resolved to {endpoint!r}; ownership must be explicit"
    )


def test_documents_deep_link_serves_shell_for_real_document():
    """A deep link to a REAL document must serve the SPA shell — never crash.

    documents_detail used to render the never-created template "documents.html",
    so any existing document id produced a TemplateNotFound crash (500) in
    production. The SPA owns document rendering; the server serves the shell.
    """
    app = _app()
    with app.app_context():
        from app import db
        from app.models import Document

        db.create_all()
        doc = Document(tenant_id=1, filename="deep-link.pdf",
                       file_path="/tmp/deep-link.pdf", file_type="pdf",
                       classification="other")
        db.session.add(doc)
        db.session.commit()
        doc_id = doc.id

    with app.test_client() as client:
        resp = client.get(f"/documents/{doc_id}")

    assert resp.status_code == 200, (
        f"GET /documents/{doc_id} returned {resp.status_code}; the deep link "
        "must serve the SPA shell (200), never crash on a missing template"
    )
    html = resp.get_data(as_text=True).lower()
    assert "shunya" in html, "Response must contain the SPA shell, not an error page"


def test_documents_upload_route_intact():
    """POST /documents/upload keeps its own route — untouched by de-duplication."""
    endpoint, _ = _app().url_map.bind("localhost").match(
        "/documents/upload", method="POST")
    assert endpoint == "main.documents_upload"


def test_legacy_fallback_surface_still_resolves_after_dedup():
    """De-duplicating /documents must not break the rest of the legacy surface.

    Each remaining legacy path must still resolve to SOME handler (dedicated
    route or the fallback) and must not be hijacked by the documents handlers.
    The resolved endpoints are recorded in the assertion output.
    """
    adapter = _app().url_map.bind("localhost")
    legacy_paths = (
        "/leads", "/leads/new", "/invoices", "/payments", "/tasks",
        "/calendar", "/reports", "/team", "/pipeline", "/settings",
        "/itineraries",
    )
    resolutions = {}
    for path in legacy_paths:
        endpoint, _ = adapter.match(path, method="GET")
        resolutions[path] = endpoint
        assert endpoint, f"{path} no longer resolves after de-duplication"
        assert not endpoint.startswith("main.documents_"), (
            f"{path} is now routed through a documents handler ({endpoint!r}) — "
            "the de-duplication inverted ownership"
        )
    print(f"LEGACY SURFACE RESOLUTIONS: {resolutions}")
