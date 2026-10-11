"""r6b28 — safety governance: age verification fields on team_members

Adds birth_date (self-declared, nullable) and age_verified (recorded by an
authorized admin after an external age-verification process) so the SHUNYA
safety gate can distinguish UNKNOWN / UNVERIFIED / UNDERAGE / VERIFIED
identities instead of treating every account as unverifiable.

Safe additive migration: no backfill, no data rewrite, no constraint on
existing rows (both columns nullable or defaulted).
"""

revision = "r6b28_age_verification_fields"
down_revision = "c_tenancy_fk_convergence_tier2"

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column(
        "team_members",
        sa.Column("birth_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "team_members",
        sa.Column(
            "age_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("team_members", "age_verified")
    op.drop_column("team_members", "birth_date")