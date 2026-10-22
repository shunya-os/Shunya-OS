"""G1.21 — onboarding questionnaire, resume and first meaningful object.

G1.20 listed the onboarding questionnaire/resume walkthrough as *not tested*. It is
tested here against the real app, with real sessions:

  1. fresh signup
  2. email verification through the established test mechanism (verify_token)
  3. login
  4. organization creation
  5. workspace provisioning
  6. the onboarding questionnaire itself (real endpoints, real steps)
  7. save + resume after a reload / new session / lost process cache
  8. completion and transition to a usable application
  9. first meaningful business-data creation
 10. persistence, list/detail visibility and restored state after reload
 11. abandoned and repeated submissions (no duplicate orgs, workspaces,
     placeholders or memberships)

The resume assertions deliberately clear the module-level cache and start a new
login: G1.21 replaced process-local step state with
``user_profiles.onboarding_step``, and the only way to prove that is to make the
process memory useless.
"""

import uuid

import pytest

from app import db

PASSWORD = "G1.21-onboarding-password"
ID = "/api/v1/orgs"


def _signup(client, tag):
    from app.auth import TeamMember

    email = f"{tag}-{uuid.uuid4().hex[:8]}@g121.test"
    response = client.post("/api/v1/auth/signup", json={
        "name": tag, "email": email, "password": PASSWORD,
    })
    assert response.status_code in (200, 201), response.get_data(as_text=True)
    member = TeamMember.query.filter_by(email=email).first()
    assert member is not None
    return email, member


def _verify(client, member):
    if member.verified:
        return
    response = client.post("/api/v1/auth/verify-email", json={"token": member.verify_token})
    assert response.status_code == 200, response.get_data(as_text=True)


def _login(client, email):
    response = client.post("/login/password", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.get_data(as_text=True)
    with client.session_transaction() as sess:
        return sess.get("identity_id")


def _status(client):
    response = client.get(f"{ID}/onboarding/status")
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["data"]


def _step(client, step):
    response = client.put(f"{ID}/onboarding/step/{step}")
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["data"]


class TestOnboardingJourney:
    def test_signup_verify_login_org_workspace_questionnaire_resume_and_first_object(
            self, client, app):
        from app.models import OrgMember
        from app.objects.legacy_models import Workspace
        from app.production.identity import onboarding_routes

        # ---- 1/2/3. signup → verify → login ---------------------------------
        email, member = _signup(client, "g121_onb")
        _verify(client, member)
        identity = _login(client, email)
        assert identity

        # ---- 4/5. organization + workspace ----------------------------------
        created = client.post("/orgs", json={"company_name": "Onboarding Journey Co"})
        assert created.status_code == 201, created.get_data(as_text=True)
        org_id = int(created.get_json()["org_id"])
        workspace_id = created.get_json()["workspace_id"]
        assert workspace_id

        workspaces = Workspace.query.filter_by(organization_id=org_id).all()
        assert len(workspaces) == 1
        assert workspaces[0].id == workspace_id
        membership = OrgMember.query.filter_by(
            organization_id=org_id, identity_id=workspaces[0].created_by).first() or \
            OrgMember.query.filter_by(organization_id=org_id).first()
        assert membership is not None

        # ---- 6. the questionnaire itself -------------------------------------
        state = _status(client)
        assert state["current_step"] == "profile"
        assert state["completed_steps"] == []
        assert state["is_complete"] is False
        assert state["all_steps"] == ["profile", "org_setup", "invite_team",
                                      "workspace", "complete"]

        assert _step(client, "profile")["current_step"] == "profile"
        after_org_setup = _step(client, "org_setup")
        assert after_org_setup["current_step"] == "org_setup"
        assert "profile" in after_org_setup["completed_steps"]

        # invalid step is refused and changes nothing
        bad = client.put(f"{ID}/onboarding/step/not_a_step")
        assert bad.status_code == 400
        assert _status(client)["current_step"] == "org_setup"

        # ---- 7. resume after reload / new session / lost process cache -------
        onboarding_routes._ONBOARDING.clear()   # the process forgot everything
        _client_logout(client)
        identity = _login(client, email)
        assert identity
        resumed = _status(client)
        assert resumed["current_step"] == "org_setup", (
            "onboarding did not resume from durable state: " f"{resumed}")
        assert "profile" in resumed["completed_steps"]

        assert _step(client, "invite_team")["current_step"] == "invite_team"
        assert _step(client, "workspace")["current_step"] == "workspace"

        # ---- 8. completion ---------------------------------------------------
        completed = client.post(f"{ID}/onboarding/complete")
        assert completed.status_code == 200, completed.get_data(as_text=True)
        body = completed.get_json()["data"]
        assert body["onboarding_completed"] is True
        assert body["objects_created"] == 26, body

        assert _status(client)["is_complete"] is True
        assert client.get(f"{ID}/onboarding/check").get_json()["data"][
            "onboarding_completed"] is True

        # ---- 8b. repeated completion must not duplicate placeholders ---------
        again = client.post(f"{ID}/onboarding/complete")
        assert again.status_code == 200
        assert again.get_json()["data"]["objects_created"] == 0, (
            "repeated completion duplicated the foundational placeholders")

        listing = client.get("/api/v1/objects")
        assert listing.status_code == 200, listing.get_data(as_text=True)
        assert listing.get_json()["total"] == 26

        # --- first-use semantics after G1.24 (D-1 = Option B) ------------------
        # 26 provisioned placeholders and zero user-supplied records: the tenant
        # has NO business data. The examples still exist and are still listed —
        # they demonstrate the workspace — but they are excluded from the
        # predicate and labelled as examples.
        placeholder_state = client.get("/api/v1/objects/first-object-state").get_json()
        assert placeholder_state["has_business_data"] is False, (
            "PROVISIONED PLACEHOLDERS WERE COUNTED AS USER BUSINESS DATA — "
            "G1.24 decision D-1 (Option B) requires them to be excluded")
        assert placeholder_state["total"] == 0, placeholder_state
        assert placeholder_state["counts"]["examples"] == 26, placeholder_state

        listed = listing.get_json()["objects"]
        assert all(o.get("provenance") == "onboarding_seed" for o in listed), (
            "provisioned rows must record their origin; unmarked rows would be "
            "counted as user data and become AI facts")
        assert all(o.get("is_example") is True for o in listed)
        assert all(o.get("content") in (None, "") for o in listed), (
            "provisioned placeholders are expected to be empty")

        # ---- 9. first meaningful object --------------------------------------
        made = client.post("/api/v1/objects/",
                           json={"name": "First real customer", "object_type": "customer"})
        assert made.status_code == 200, made.get_data(as_text=True)
        object_id = made.get_json()["object_id"]
        assert made.get_json()["success"] is True

        # ---- 10. persistence + visibility after reload -----------------------
        _client_logout(client)
        _login(client, email)

        listing = client.get("/api/v1/objects")
        assert listing.status_code == 200
        names = [o["name"] for o in listing.get_json()["objects"]]
        assert "First real customer" in names

        detail = client.get(f"/api/v1/objects/by-id/{object_id}")
        assert detail.status_code == 200, detail.get_data(as_text=True)

        state = client.get("/api/v1/objects/first-object-state").get_json()
        assert state["has_business_data"] is True

        # exactly one real customer named that, plus the one placeholder
        assert names.count("First real customer") == 1

    def test_abandoned_onboarding_can_be_reset_and_restarted(self, client, app):
        from app.production.identity import onboarding_routes

        email, member = _signup(client, "g121_onb_reset")
        _verify(client, member)
        _login(client, email)
        assert client.post("/orgs", json={"company_name": "Reset Co"}).status_code == 201

        _step(client, "profile")
        _step(client, "org_setup")
        assert _status(client)["current_step"] == "org_setup"

        reset = client.post(f"{ID}/onboarding/reset")
        assert reset.status_code == 200
        onboarding_routes._ONBOARDING.clear()
        _client_logout(client)
        _login(client, email)

        fresh = _status(client)
        assert fresh["current_step"] == "profile", fresh
        assert fresh["completed_steps"] == []
        assert fresh["is_complete"] is False

        # restart works after the reset
        assert _step(client, "profile")["current_step"] == "profile"
        assert client.post(f"{ID}/onboarding/complete").status_code == 200

    def test_repeated_org_creation_does_not_duplicate_workspaces(self, client, app):
        from app.objects.legacy_models import Workspace

        email, member = _signup(client, "g121_onb_dupe")
        _verify(client, member)
        _login(client, email)

        first = client.post("/orgs", json={"company_name": "Repeat Co"})
        second = client.post("/orgs", json={"company_name": "Repeat Co"})
        assert first.status_code == 201 and second.status_code == 201

        org_a = int(first.get_json()["org_id"])
        org_b = int(second.get_json()["org_id"])
        assert org_a != org_b, "two deliberate requests are two organizations"

        for org_id in (org_a, org_b):
            rows = Workspace.query.filter_by(organization_id=org_id, status="active").all()
            assert len(rows) == 1, f"org {org_id} has {len(rows)} workspaces"

        # With two authorized organizations and none selected, the read surface
        # must fail closed with a truthful 403 — never a 500, never a false empty
        # state. (This is the regression guard for the malformed 1-tuple denial.)
        ambiguous = client.get("/api/v1/objects")
        assert ambiguous.status_code == 403, ambiguous.get_data(as_text=True)
        body = ambiguous.get_json()
        assert body and body.get("success") is False
        assert body.get("code"), "denial must carry a machine-readable reason"

        # Selecting an organization makes the same surface usable.
        scoped = client.get("/api/v1/objects",
                            headers={"X-Organization-Id": str(org_a)})
        assert scoped.status_code == 200, scoped.get_data(as_text=True)

        # Repeated completion must not duplicate placeholders in either tenant.
        assert client.post(f"{ID}/onboarding/complete").status_code == 200
        total_after_first = client.get(
            "/api/v1/objects", headers={"X-Organization-Id": str(org_a)}).get_json()["total"]
        assert client.post(f"{ID}/onboarding/complete").status_code == 200
        total_after_second = client.get(
            "/api/v1/objects", headers={"X-Organization-Id": str(org_a)}).get_json()["total"]
        assert total_after_second == total_after_first, (
            "repeated onboarding completion duplicated foundational objects")


def _client_logout(client):
    """Log out through the real endpoint (session must not be forged).

    ``/logout`` is a GET route owned by the auth blueprint; the method is
    asserted here so a future change to POST-only is noticed by this journey.
    """
    response = client.get("/logout")
    assert response.status_code in (200, 302, 204), response.status_code


class TestQuestionnaireResume:
    """The Universal Business Discovery questionnaire (/api/v1/onboarding)."""

    def test_answers_survive_losing_process_memory(self, client, app):
        from app.onboarding import engine
        from app.onboarding.models import OnboardingSessionState

        email, member = _signup(client, "g121_q")
        _verify(client, member)
        _login(client, email)
        created = client.post("/orgs", json={"company_name": "Questionnaire Co"})
        assert created.status_code == 201
        org_id = int(created.get_json()["org_id"])

        started = client.post("/api/v1/onboarding/start")
        assert started.status_code == 200, started.get_data(as_text=True)
        body = started.get_json()
        assert body["status"] == "started"
        assert body["question"]["key"] == "company_name", body["question"]

        first = client.post("/api/v1/onboarding/answer",
                            json={"key": "company_name", "value": "Questionnaire Co"})
        assert first.status_code == 200, first.get_data(as_text=True)
        assert first.get_json()["next_question"]["key"] == "industry"

        # Simulate the real hazard: a reload served by another worker, i.e. the
        # process-local cache is gone.
        engine._sessions.clear()

        resumed = client.post("/api/v1/onboarding/start")
        assert resumed.status_code == 200, resumed.get_data(as_text=True)
        question = resumed.get_json()["question"]
        assert question["key"] == "industry", (
            "questionnaire did not resume from durable state: " f"{question}")

        row = OnboardingSessionState.query.filter_by(
            organization_id=org_id).first()
        assert row is not None, "answers were not persisted"
        assert "company_name" in row.answers_json

        # a reset clears the durable row too
        assert client.post("/api/v1/onboarding/reset").status_code == 200
        engine._sessions.clear()
        fresh = client.post("/api/v1/onboarding/start")
        assert fresh.get_json()["question"]["key"] == "company_name"
        assert OnboardingSessionState.query.filter_by(
            organization_id=org_id).first() is None
