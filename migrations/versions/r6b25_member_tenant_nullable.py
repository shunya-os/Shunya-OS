"""R6B-2.5 — team_members.tenant_id becomes nullable (no implicit tenant).

A team member has no tenant at signup. Canonical tenancy is established through
OrgMember once the user joins an organization. The account-creation path
previously wrote an arbitrary default tenant (tenant 1) purely to satisfy a NOT
NULL constraint, which silently placed every new account inside a tenant it had
never joined.

With the application no longer writing that default, the column must permit
"no tenant". This revision is additive and backward compatible: existing rows
keep their values, and on a database whose model baseline already declares the
column nullable it is a no-op.

NOTE: the revision id must stay within 32 characters — Alembic stores it in
alembic_version.version_num, which is character varying(32).

Revision ID: r6b25_member_tenant_nullable
Revises: g1_1_r6b_ownership
"""
from alembic import op

revision = "r6b25_member_tenant_nullable"
down_revision = "g1_1_r6b_ownership"
branch_labels = None
depends_on = None


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    if op.has_column("team_members", "tenant_id"):
        op.alter_column("team_members", "tenant_id", nullable=True)
        print("  team_members.tenant_id -> nullable (no implicit tenant)")


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    if op.has_column("team_members", "tenant_id"):
        op.alter_column("team_members", "tenant_id", nullable=False)
