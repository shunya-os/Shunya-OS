"""r6b38 — persist creation provenance on canonical objects (G1.24, D-1 = B).

WHY
---
Onboarding provisions 26 placeholder ("example") objects so a new workspace is
not visually empty. Nothing recorded that fact, so the first-use predicate and
the AI grounding path could only count rows — and they counted the examples. A
brand-new tenant therefore reported ``has_business_data: true`` with zero user
input, and the assistant could present "Customer", "Invoice", … as organizational
facts (decision D-2 = No).

Adding the marker after the fact is not possible: an edited placeholder and an
unused one are indistinguishable once written. The origin has to be stored at
creation time.

WHAT
----
One nullable column:

    sh_objects.provenance  VARCHAR(32)  user | import | ai | onboarding_seed
                                         | system | NULL (unknown history)

Additive and guarded:

* No default, no NOT NULL. Existing rows keep NULL = *unknown*, which the
  predicate and the grounding boundary both treat as ordinary business data.
  Guessing would either hide a tenant's real records or launder examples into
  facts; neither is acceptable.
* No backfill. The 26-row seed signature is *suggestive* but not proof (a user
  can create a record named "Customer" with empty content), so converting
  historical rows is left to an operator procedure with evidence, not to a
  migration that runs unattended on production.
* No index. The first-use query filters by ``organization_id`` (already indexed)
  plus ``is_deleted``; there is no measured execution plan showing a provenance
  index is needed, and unproven indexes are cost without a proven query.

Revision ID: r6b38_object_provenance
Revises: r6b37_onboarding_sessions
"""
import sqlalchemy as sa
from alembic import op  # noqa: F401

revision = "r6b38_object_provenance"
down_revision = "r6b37_onboarding_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from migrations.guarded import guarded_op

    gop = guarded_op()
    gop.add_column(
        "sh_objects",
        sa.Column("provenance", sa.String(32), nullable=True),
    )


def downgrade() -> None:
    from migrations.guarded import guarded_op

    gop = guarded_op()
    gop.drop_column("sh_objects", "provenance")
