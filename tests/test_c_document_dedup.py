"""C-stage — document upload: duplicate detection on real bytes.

Observed live during the Stage C browser round: re-adding the same file created
a second row and a second blob (no duplicate detection existed — a required
support in the Stage C contract). Uploads now hash the bytes while saving and
return the existing record truthfully when identical content is already in the
caller's tenant scope.

Also: the PDF extraction subprocess no longer embeds the caller's filename in
Python source — it runs an argv-based module with the venv interpreter.
"""

import io
import os
import subprocess
import sys

import pytest

PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF"
)


@pytest.fixture(scope="function")
def app():
    from app import create_app, db
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
        "DISABLE_RATE_LIMIT": True,
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def auth(app, client):
    """Seed org/member/RBAC + session context so the ingest route authorizes."""
    from app import db
    from app.models import Organization, OrgMember
    from app.auth import TeamMember
    from app.authz.services import seed_default_roles

    org_id = 989
    identity = "c_stage_tester"
    user_id = 4242

    org = db.session.get(Organization, org_id)
    if not org:
        org = Organization(id=org_id, name="C Stage Org",
                           slug="c-stage", is_active=True)
        db.session.add(org)
        db.session.flush()
    seed_default_roles(org_id)

    member = OrgMember.query.filter_by(
        organization_id=org_id, identity_id=identity).first()
    if not member:
        db.session.add(OrgMember(organization_id=org_id, identity_id=identity,
                                 role="owner", is_active=True))

    tm = db.session.get(TeamMember, user_id)
    if not tm:
        db.session.add(TeamMember(id=user_id, tenant_id=org_id,
                                  name="C Stage", email="cstage@example.com"))
    db.session.commit()

    with client.session_transaction() as s:
        s["identity_id"] = identity
        s["user_id"] = user_id
        s["current_org_id"] = org_id
    return {"identity_id": identity, "org_id": org_id}


def _upload(client, name, content):
    return client.post(
        "/api/v1/founder/ingest",
        data={"file": (io.BytesIO(content), name)},
        content_type="multipart/form-data",
    )


def test_same_bytes_twice_is_reported_as_duplicate(app, client, auth):
    from app.models import Document

    r1 = _upload(client, "c_stage_doc.pdf", PDF_BYTES)
    assert r1.status_code == 200
    b1 = r1.get_json()
    assert b1["success"] is True
    assert b1.get("duplicate") is not True
    assert Document.query.count() == 1

    r2 = _upload(client, "c_stage_doc_again.pdf", PDF_BYTES)
    assert r2.status_code == 200
    b2 = r2.get_json()
    assert b2["success"] is True
    assert b2.get("duplicate") is True
    assert b2["document_id"] == b1["document_id"]
    assert "already" in b2["summary"].lower()
    assert Document.query.count() == 1, "duplicate upload must not create a second row"


def test_different_bytes_are_not_duplicates(app, client, auth):
    from app.models import Document

    _upload(client, "c_stage_one.pdf", PDF_BYTES)
    r = _upload(client, "c_stage_two.pdf", PDF_BYTES + b"\n%extra")
    assert r.get_json().get("duplicate") is not True
    assert Document.query.count() == 2


def test_uploaded_document_records_content_hash(app, client, auth):
    import hashlib

    from app.models import Document

    _upload(client, "c_stage_hash.pdf", PDF_BYTES)
    doc = Document.query.first()
    assert doc.content_sha256 == hashlib.sha256(PDF_BYTES).hexdigest()


def test_extract_cli_uses_argv_and_reports_truthfully(tmp_path):
    """The subprocess replacement: argv-based, venv interpreter, truthful marker."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 this is not really a pdf")

    res = subprocess.run(
        [sys.executable, "-m", "app.document.extract_cli", str(broken)],
        capture_output=True, text=True, timeout=60, cwd=repo_root,
    )
    assert res.returncode == 0
    out = res.stdout.strip()
    assert out.startswith(("[extraction", "No text could be extracted")), (
        f"a broken PDF must degrade truthfully, got: {out[:120]!r}")


def test_extract_cli_requires_a_path():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res = subprocess.run(
        [sys.executable, "-m", "app.document.extract_cli"],
        capture_output=True, text=True, timeout=60, cwd=repo_root,
    )
    assert res.returncode == 2
    assert "usage" in res.stderr.lower()