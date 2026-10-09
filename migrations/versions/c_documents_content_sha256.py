"""C-stage — documents.content_sha256: canonical content identity for duplicate detection.

WHY
---
The document upload path (POST /api/v1/founder/ingest) had no duplicate
detection: re-adding the same file created a second row and a second blob.
The Stage C contract requires "Duplicate detection" as first-class support, so
the content bytes need a canonical identity — a SHA-256 of the file.

WHAT
----
Idempotent, guarded, data-preserving:
  1. add ``documents.content_sha256`` (nullable String(64)) when absent;
  2. add a non-unique index for scoped duplicate lookups.

Existing rows keep NULL (their files are not re-hashed here — a deliberate
choice: migrations must not read arbitrary filesystem state). The upload
handler fills the value for every new upload; a re-upload of a pre-migration
file is therefore only detected after that file is added once more.

Revision ID: c_documents_content_sha256
Revises: m6_supplier_tenancy_retarget
"""
import sqlalchemy as sa

revision = "c_documents_content_sha256"
down_revision = "m6_supplier_tenancy_retarget"
branch_labels = None
depends_on = None


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    if not op.has_table("documents"):
        print("  documents: table absent — nothing to do")
        return

    if not op.has_column("documents", "content_sha256"):
        op.add_column("documents", sa.Column("content_sha256", sa.String(64), nullable=True))
        print("  documents: column content_sha256 added")
    else:
        print("  documents: column content_sha256 already present")

    if not op.has_index("ix_documents_content_sha256"):
        op.create_index("ix_documents_content_sha256", "documents", ["content_sha256"])
        print("  documents: index ix_documents_content_sha256 created")
    else:
        print("  documents: index ix_documents_content_sha256 already present")


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    if not op.has_table("documents"):
        return

    if op.has_index("ix_documents_content_sha256"):
        op.drop_index("ix_documents_content_sha256", table_name="documents")

    if op.has_column("documents", "content_sha256"):
        op.drop_column("documents", "content_sha256")