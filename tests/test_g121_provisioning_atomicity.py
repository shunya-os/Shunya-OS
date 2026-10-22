"""G1.21 — atomicity of organization + workspace provisioning.

The G1.19/G1.20 invariant is: *every organization owns at least one active
canonical workspace with an owner membership from the moment it is created*.
That invariant is only worth anything if a failure part-way through cannot leave
half a tenant behind.

These tests do not trust that. They inject a real failure at each transaction
boundary of ``POST /orgs`` — using SQLAlchemy session events, so the failure
happens inside the live unit of work, not in a mocked helper — and then inspect
the database with raw SQL through the application's own engine (a connection that
knows nothing about the ORM session) to see what actually survived.

Boundaries covered:
  1. after the organization row is inserted
  2. after the owner membership row is added
  3. after the default roles are seeded
  4. after the canonical workspace row is created
  5. after the workspace membership row is added
  6. immediately before commit
  7. a retry of the same logical request after an interrupted attempt

For every boundary the assertions are the same: no partial rows, and the retry
succeeds exactly once — no duplicate organization, workspace, membership or role.

No test-only failure switch exists in production code: the injection lives
entirely in this file, on the SQLAlchemy ``Session`` class, and is removed in a
``finally`` block.
"""

from contextlib import contextmanager

import pytest
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from app import db

PASSWORD = "G1.21-atomicity-password"


class InjectedFailure(RuntimeError):
    """A deliberate failure raised inside the unit of work."""


@contextmanager
def inject_failure_on(model, when="after_flush", only_when=None, state=None):
    """Raise :class:`InjectedFailure` when ``model`` enters the unit of work.

    ``when`` is a SQLAlchemy Session event (``after_flush`` / ``before_flush``).
    ``only_when`` optionally receives the pending instance and returns False to
    let that particular insert through (used to inject on the *second* workspace
    membership, for example).

    ``state`` is an optional dict that records what was pending in the unit of
    work at the moment of injection. That record is what makes the post-request
    "no rows survived" assertion meaningful: it proves the transaction really did
    contain the organization/workspace/membership rows, so their absence
    afterwards is a rollback and not an empty test.
    """
    if state is None:
        state = {}

    def handler(session, *args):
        for obj in list(session.new):
            if isinstance(obj, model) and (only_when is None or only_when(obj)):
                state["fired"] = True
                state["boundary_model"] = type(obj).__name__
                state["pending"] = sorted(
                    {type(o).__name__ for o in list(session.new)})
                # The organization may already have been flushed (so it is in the
                # identity map, not in ``new``); record that the tenant really is
                # in this unit of work either way.
                state["org_in_unit_of_work"] = any(
                    type(o).__name__ == "Organization"
                    for o in list(session.new) + list(session.identity_map.values()))
                raise InjectedFailure(
                    f"injected failure at {when} for {model.__name__}")
    state["fired"] = False
    event.listen(Session, when, handler)
    try:
        yield state
    finally:
        event.remove(Session, when, handler)


@contextmanager
def inject_failure_before_commit(state=None):
    """Raise immediately before COMMIT is issued, after everything is flushed."""
    if state is None:
        state = {}

    def handler(session):
        # ``POST /orgs`` commits twice: once for identity canonicalisation (before
        # any Organization exists) and once for the tenant transaction. Only the
        # second commit is the boundary under test — firing on the first would
        # measure the wrong transaction.
        in_uow = any(
            type(o).__name__ == "Organization"
            for o in list(session.new) + list(session.identity_map.values()))
        if not in_uow:
            return
        state["fired"] = True
        state["boundary_model"] = "commit"
        state["pending"] = sorted({type(o).__name__ for o in list(session.new)})
        state["org_in_unit_of_work"] = True
        raise InjectedFailure("injected failure immediately before commit")
    state["fired"] = False
    event.listen(Session, "before_commit", handler)
    try:
        yield state
    finally:
        event.remove(Session, "before_commit", handler)


@contextmanager
def request_scope(app):
    """Run a request the way production does: its own application context.

    The ``app`` fixture leaves an application context open for the whole test.
    Flask-SQLAlchemy removes (and therefore rolls back) the session on *app
    context* teardown, so a request issued inside the fixture's context would
    never be cleaned up: the failed transaction would survive into the retry and
    the test would measure the test harness, not the product. Entering a fresh
    context here reproduces the real per-request lifecycle.

    ``PROPAGATE_EXCEPTIONS=False`` makes Flask render the error response a real
    caller would receive instead of re-raising (the test app runs with
    TESTING=True, which would otherwise surface the exception).
    """
    previous = app.config.get("PROPAGATE_EXCEPTIONS")
    app.config["PROPAGATE_EXCEPTIONS"] = False
    try:
        with app.app_context():
            yield
    finally:
        app.config["PROPAGATE_EXCEPTIONS"] = previous
        db.session.expire_all()


def _counts():
    """Row counts read with raw SQL on the app's engine (not through the ORM)."""
    out = {}
    with db.engine.connect() as conn:
        for table in ("organizations", "org_members", "sh_workspaces",
                      "sh_workspace_memberships", "auth_roles", "founder_spaces"):
            out[table] = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar()
    return out


def _new_user(client, tag):
    from app.auth import TeamMember

    email = f"{tag}@g121.test"
    signup = client.post("/api/v1/auth/signup", json={
        "name": tag, "email": email, "password": PASSWORD,
    })
    assert signup.status_code in (200, 201), signup.get_data(as_text=True)

    member = TeamMember.query.filter_by(email=email).first()
    assert member is not None
    if not member.verified:
        verified = client.post("/api/v1/auth/verify-email",
                               json={"token": member.verify_token})
        assert verified.status_code == 200, verified.get_data(as_text=True)

    login = client.post("/login/password", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.get_data(as_text=True)
    return email


def _org_rows():
    with db.engine.connect() as conn:
        return conn.execute(text(
            "SELECT o.id, o.name, o.slug,"
            " (SELECT count(*) FROM sh_workspaces w WHERE w.organization_id = o.id),"
            " (SELECT count(*) FROM org_members m WHERE m.organization_id = o.id)"
            " FROM organizations o ORDER BY o.id")).fetchall()


class TestFaultInjectionLeavesNoPartialState:
    """One test per transaction boundary, plus the retry that follows it."""

    def _boundary(self, client, app, tag, model_name, when="after_flush", only_when=None,
                  before_commit=False):
        from app.models import Organization, OrgMember
        from app.objects.legacy_models import Workspace, ShWorkspaceMembership
        from app.authz.models import Role

        models = {
            "Organization": Organization,
            "OrgMember": OrgMember,
            "Role": Role,
            "Workspace": Workspace,
            "ShWorkspaceMembership": ShWorkspaceMembership,
        }

        _new_user(client, tag)
        before = _counts()

        cm = (inject_failure_before_commit() if before_commit
              else inject_failure_on(models[model_name], when=when, only_when=only_when))
        with request_scope(app):
            with cm as state:
                response = client.post("/orgs", json={"company_name": f"{tag} Holdings"})

        # 0. the injection really happened inside the unit of work, and the
        #    transaction really contained tenant rows at that moment. Without
        #    this, "no rows afterwards" could mean "no rows were ever written".
        assert state.get("fired") is True, (
            f"failure was never injected for {model_name}/{when} — "
            "the test would prove nothing")
        if model_name is not None:
            assert state["boundary_model"] == model_name
        assert state.get("org_in_unit_of_work") is True, (
            "the organization was not part of the unit of work at injection: "
            f"pending={state.get('pending')}")

        # 1. the caller is told the truth: an error, not a success
        assert response.status_code >= 400, (
            f"injected failure produced {response.status_code}: "
            f"{response.get_data(as_text=True)[:400]}")
        body = response.get_json(silent=True) or {}
        assert body.get("success") is not True

        # 2. nothing half-written survived the request
        after = _counts()
        assert after == before, (
            f"partial state after injected failure at {model_name}/{when}: "
            f"before={before} after={after}")

        # 3. the same logical request can be retried, and succeeds exactly once
        retry = client.post("/orgs", json={"company_name": f"{tag} Holdings"})
        assert retry.status_code == 201, retry.get_data(as_text=True)
        org_id = int(retry.get_json()["org_id"])

        rows = _org_rows()
        matching = [r for r in rows if r[0] == org_id]
        assert len(matching) == 1
        assert matching[0][3] == 1, "retry must provision exactly one workspace"
        assert matching[0][4] == 1, "retry must create exactly one owner membership"

        # 4. no duplicate organization was left behind by the failed attempt
        names = [r[1] for r in rows]
        assert names.count(f"{tag} Holdings") == 1

        with db.engine.connect() as conn:
            # organization_id IS NOT NULL: the three system workspaces
            # (spc_business/spc_personal/spc_custom) deliberately carry no
            # organization and are not tenant duplicates.
            dup_ws = conn.execute(text(
                "SELECT organization_id, count(*) FROM sh_workspaces "
                "WHERE organization_id IS NOT NULL "
                "GROUP BY organization_id HAVING count(*) > 1")).fetchall()
            dup_mem = conn.execute(text(
                "SELECT organization_id, identity_id, count(*) FROM org_members "
                "GROUP BY organization_id, identity_id HAVING count(*) > 1")).fetchall()
            dup_roles = conn.execute(text(
                "SELECT organization_id, name, count(*) FROM auth_roles "
                "GROUP BY organization_id, name HAVING count(*) > 1")).fetchall()
        assert dup_ws == [], f"duplicate workspaces: {dup_ws}"
        assert dup_mem == [], f"duplicate memberships: {dup_mem}"
        assert dup_roles == [], f"duplicate roles: {dup_roles}"

    def test_failure_after_organization_insert(self, client, app):
        self._boundary(client, app, "g121_fail_org", "Organization")

    def test_failure_after_owner_membership(self, client, app):
        self._boundary(client, app, "g121_fail_member", "OrgMember")

    def test_failure_after_default_roles(self, client, app):
        self._boundary(client, app, "g121_fail_roles", "Role")

    def test_failure_after_workspace_creation(self, client, app):
        self._boundary(client, app, "g121_fail_ws", "Workspace")

    def test_failure_after_workspace_membership(self, client, app):
        self._boundary(client, app, "g121_fail_ws_member", "ShWorkspaceMembership")

    def test_failure_immediately_before_commit(self, client, app):
        self._boundary(client, app, "g121_fail_commit", None, before_commit=True)


class TestUniquenessUnderCompetingCreation:
    def test_two_organizations_with_the_same_name_get_distinct_slugs(self, client, app):
        """The slug is the organization's URL identity: unique, but never a 500."""
        _new_user(client, "g121_slug")
        first = client.post("/orgs", json={"company_name": "Shared Name Co"})
        second = client.post("/orgs", json={"company_name": "Shared Name Co"})
        assert first.status_code == 201, first.get_data(as_text=True)
        assert second.status_code == 201, second.get_data(as_text=True)

        with db.engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT id, slug FROM organizations WHERE name = 'Shared Name Co' "
                "ORDER BY id")).fetchall()
        assert len(rows) == 2
        assert rows[0][1] != rows[1][1], f"slugs collided: {rows}"
        assert rows[0][1] == "shared-name-co"
        assert rows[1][1].startswith("shared-name-co-")

    def test_slug_collision_at_commit_is_a_truthful_conflict(self, client, app):
        """A race past the pre-flight check must not surface as a stack trace."""
        from app.models import Organization

        _new_user(client, "g121_slug_race")
        existing = Organization(name="Race Co", slug="race-co")
        db.session.add(existing)
        db.session.commit()

        # Simulate the race: make the uniqueness probe miss, so the insert really
        # collides with the unique index at commit time.
        import app.authz.org_slug as slug_mod

        original = slug_mod.ensure_unique_org_slug
        slug_mod.ensure_unique_org_slug = lambda base, max_length=120: "race-co"
        try:
            with request_scope(app):
                response = client.post("/orgs", json={"company_name": "Race Co"})
        finally:
            slug_mod.ensure_unique_org_slug = original

        assert response.status_code in (409, 400), response.get_data(as_text=True)
        body = response.get_json()
        assert body.get("success") is False

        with db.engine.connect() as conn:
            n = conn.execute(text(
                "SELECT count(*) FROM organizations WHERE slug = 'race-co'")).scalar()
            orgs = conn.execute(text(
                "SELECT count(*) FROM organizations WHERE name = 'Race Co'")).scalar()
        assert n == 1, "the conflicting insert must not be persisted"
        assert orgs == 1


class TestAtomicityContractIsExplicit:
    def test_counts_probe_is_sensitive_to_committed_rows(self, client, app):
        """Control for the fault-injection assertions.

        The rollback tests conclude "nothing was written" from unchanged counts.
        That conclusion is only meaningful if the same probe *does* see rows when
        the transaction commits. This control commits a normal organization and
        asserts the probe moves — so a passing rollback test cannot be an artefact
        of a blind counter.
        """
        _new_user(client, "g121_control")
        before = _counts()
        created = client.post("/orgs", json={"company_name": "Probe Control Co"})
        assert created.status_code == 201, created.get_data(as_text=True)
        after = _counts()
        assert after["organizations"] == before["organizations"] + 1
        assert after["org_members"] == before["org_members"] + 1
        assert after["sh_workspaces"] == before["sh_workspaces"] + 1
        assert after["sh_workspace_memberships"] > before["sh_workspace_memberships"]

    def test_identity_canonicalisation_commit_is_its_own_step(self, client, app):
        """Documented boundary: ``POST /orgs`` commits the identity link first.

        That commit is deliberate (it repairs a legacy fallback identity, and it
        must survive an organization failure so the user is not left with an
        unresolvable session). Everything after it — organization, membership,
        roles, founder space, canonical workspace, workspace membership — is a
        single transaction, which the fault-injection tests above prove.
        """
        from app.auth import TeamMember

        email = _new_user(client, "g121_identity_step")
        member = TeamMember.query.filter_by(email=email).first()
        identity_before = member.identity_id

        from app.models import Organization

        with request_scope(app):
            with inject_failure_on(Organization):
                response = client.post("/orgs", json={"company_name": "Identity Step Co"})
        assert response.status_code >= 400

        db.session.expire_all()
        member = TeamMember.query.filter_by(email=email).first()
        assert member.identity_id, "the canonical identity link must survive"
        assert identity_before is None or member.identity_id == identity_before
