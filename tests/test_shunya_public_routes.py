"""Route tests for SHUNYA public audit PDF endpoints (shunya_public.py).

NOTE: These tests use the full conftest.py app fixture rather than a minimal
Flask app, ensuring the application blueprints are properly registered and
the audit/ directory is accessible relative to the project root.
"""
import pytest

AUDIT_PDFS = [
    "/audit/lx06",
    "/audit/lx06/frontend",
    "/audit/lx06/backend",
    "/audit/lx06a",
    "/audit/pattern-language",
    "/audit/engineering-constitution",
    "/audit/mx01-phase1",
    "/audit/mx01a",
]


@pytest.mark.parametrize("path", AUDIT_PDFS)
def test_audit_pdf_serves_valid_pdf(client, path):
    r = client.get(path)
    assert r.status_code == 200, f"Expected 200 for {path}, got {r.status_code}"
    assert r.mimetype == "application/pdf"
    assert r.data[:4] == b"%PDF"
    assert len(r.data) > 1000


def test_unknown_audit_returns_404(client):
    assert client.get("/audit/does-not-exist").status_code == 404


# ── Generic catch-all route (serves any PDF from audit/ by slug) ──

GENERIC_PDFS = [
    "/audit/cdr-001",
    "/audit/cdr-001.pdf",
    "/audit/CDR-001",
    "/audit/CDR-001.pdf",
]


@pytest.mark.parametrize("path", GENERIC_PDFS)
def test_generic_audit_route_serves_cdr(client, path):
    r = client.get(path)
    assert r.status_code == 200, f"Expected 200 for {path}, got {r.status_code}"
    assert r.mimetype == "application/pdf"
    assert r.data[:4] == b"%PDF"
    assert len(r.data) > 1000


def test_generic_audit_route_404_for_missing(client):
    assert client.get("/audit/definitely-missing").status_code == 404