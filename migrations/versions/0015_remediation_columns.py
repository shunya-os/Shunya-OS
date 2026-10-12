"""Remediation convergence: new columns from the 53-dead-end closure batch.

Adds, guarded and idempotent (safe on any starting point):
  * g4_proposals.share_token      — token-gated proposal share page
  * commitments.reminded_at       — due-date reminder idempotency marker
  * document_records.content      — canonical posted document body
  * document_records.extracted_text — parsed text for search/AI context
  * suppliers: drop global unique(name) if present, add
    uq_suppliers_tenant_name (tenant_id, name) — per-org name uniqueness

The `fin_payments.status` column is covered by revision for2d_payment_status.

Revision ID: remediation_columns
Revises: for2d_payment_status
Create Date: 2026-10-12 12:30:00.000000
"""
from alembic import op  # noqa: F401
import sqlalchemy as sa

revision = "remediation_columns"
down_revision = "for2d_payment_status"


def upgrade():
    from migrations.guarded import guarded_op
    g = guarded_op()

    # ── g4_proposals.share_token (+ unique index) ──────────────────────
    g.add_column(
        "g4_proposals",
        sa.Column("share_token", sa.String(64), nullable=True),
    )
    g.create_index(
        "ix_g4_proposals_share_token",
        "g4_proposals",
        ["share_token"],
        unique=True,
    )

    # ── commitments.reminded_at ────────────────────────────────────────
    g.add_column(
        "commitments",
        sa.Column("reminded_at", sa.DateTime(), nullable=True),
    )

    # ── document_records.content / extracted_text ──────────────────────
    g.add_column(
        "document_records",
        sa.Column("content", sa.Text(), server_default=""),
    )
    g.add_column(
        "document_records",
        sa.Column("extracted_text", sa.Text(), server_default=""),
    )

    # ── suppliers: global unique(name) -> unique(tenant_id, name) ──────
    # The legacy uniqueness exists on production as the unique INDEX
    # ``uq_suppliers_name`` (probed: pg_indexes); earlier model variants
    # may also have created a constraint named ``suppliers_name_key``.
    # Drop whichever form is present, then add the per-org composite.
    for legacy_name in ("uq_suppliers_name", "suppliers_name_key"):
        if g.has_index(legacy_name):
            g.drop_index(legacy_name)
        if g.has_constraint(legacy_name, "suppliers"):
            g.drop_constraint(legacy_name, "suppliers")
    g.create_unique_constraint(
        "uq_suppliers_tenant_name", "suppliers", ["tenant_id", "name"]
    )


def downgrade():
    from migrations.guarded import guarded_op
    g = guarded_op()
    pass  # additive only — no destructive downgrade