"""First-object state — the authoritative empty-workspace predicate.

Canonical definition (G1.18, revised by G1.24 decision D-1 = Option B)
----------------------------------------------------------------------
An organization **has created its first business object** when it owns at least
one live **user-supplied** business record in any canonical business store:

* ``sh_objects`` — canonical universal objects, *excluding provisioned
  examples* (``provenance = 'onboarding_seed'``);
* ``rel_relationships`` — canonical relationships (customers, suppliers,
  partners) written by the import path, onboarding answers and the CRM
  surfaces;
* ``leads`` — canonical lead records;
* ``suppliers`` — canonical supplier records.

Why the example exclusion exists
--------------------------------
Onboarding provisions 26 placeholder objects ("Customer", "Invoice", …) so a new
workspace is not visually empty. Counting them made a brand-new tenant report
``has_business_data: true`` before it had entered a single fact. The fix is not
to stop provisioning (the examples are a useful product affordance) and not to
count rows differently by inspecting them: the row records its own origin in
``sh_objects.provenance``, and only rows *known* to be examples are excluded.

Unknown provenance (NULL, written before the field existed) **counts**. The
predicate must never hide a tenant's real records on a guess; over-counting is
recoverable, pretending a populated workspace is empty is not.

Why a union of stores, and not one store
---------------------------------------
``sh_uop_objects`` (``UOPObject``) is a migration-compatibility store: new
writes go to ``sh_objects`` (see ``app/objects/canonical.py``), so an empty UOP
table is never evidence that the user has created nothing. The import path
deliberately writes domain records — a customer *is* a ``CanonicalRelationship``
— and materialising a universal object for every imported row would be a second
write with no convergence contract; dual-write is not convergence. The
predicate therefore reads each authoritative store on its own terms instead of
duplicating records between them.

What this module is NOT
-----------------------
It is a read model over authoritative stores: it never creates, projects,
repairs, or migrates records, and it introduces no second source of truth for
any entity. Each store remains the sole owner of its own rows.

Lifecycle semantics
-------------------
Only **live** records count. Soft-deleted universal objects
(``is_deleted``), archived relationships, and archived leads/suppliers do not
make a workspace non-empty, because the CTA's claim is about the workspace the
user is looking at ("you have nothing yet"), not about history.

Tenant isolation
----------------
Every count is filtered by the organization (or the tenant column the store
uses) supplied by the caller. This module performs no unscoped query and
requires a positive organization id — it fails closed otherwise.
"""

from __future__ import annotations

from sqlalchemy import or_

from app import db
from app.objects.provenance import PROVENANCE_ONBOARDING_SEED


def _require_org(organization_id: int) -> int:
    if not organization_id or int(organization_id) < 1:
        raise ValueError(
            "first_object_state requires a positive organization_id; an "
            "unscoped emptiness answer would be another organization's truth."
        )
    return int(organization_id)


def _live_objects_query(organization_id: int):
    """Live, non-example canonical objects for exactly one organization."""
    from app.objects.legacy_models import ShunyaObject

    return (
        db.session.query(ShunyaObject)
        .filter(ShunyaObject.organization_id == organization_id)
        .filter(ShunyaObject.is_deleted.is_(False))
        .filter(
            or_(
                ShunyaObject.provenance.is_(None),
                ShunyaObject.provenance != PROVENANCE_ONBOARDING_SEED,
            )
        )
    )


def business_record_counts(organization_id: int) -> dict:
    """Live business-record counts for exactly one organization.

    ``examples`` is reported separately and is **not** part of the business
    total: it exists so the UI and evidence logs can say "26 examples, 0 real
    records" instead of choosing between lying and hiding the examples.
    """
    org_id = _require_org(organization_id)

    from app.objects.legacy_models import ShunyaObject
    from app.relationship.models import CanonicalRelationship
    from app.models import Lead, Supplier

    objects = _live_objects_query(org_id).count()
    examples = (
        db.session.query(ShunyaObject)
        .filter(ShunyaObject.organization_id == org_id)
        .filter(ShunyaObject.is_deleted.is_(False))
        .filter(ShunyaObject.provenance == PROVENANCE_ONBOARDING_SEED)
        .count()
    )
    relationships = (
        db.session.query(CanonicalRelationship)
        .filter(CanonicalRelationship.organization_id == org_id)
        .filter(CanonicalRelationship.status != "archived")
        .count()
    )
    leads = (
        db.session.query(Lead)
        .filter(Lead.tenant_id == org_id)
        .filter(Lead.status != "archived")
        .count()
    )
    suppliers = (
        db.session.query(Supplier)
        .filter(Supplier.tenant_id == org_id)
        .filter(Supplier.status != "archived")
        .count()
    )

    return {
        "objects": objects,
        "relationships": relationships,
        "leads": leads,
        "suppliers": suppliers,
        "examples": examples,
    }


def get_first_object_state(organization_id: int) -> dict:
    """Authoritative answer to "has this organization created anything yet?".

    ``has_business_data`` is ``True`` as soon as any canonical store holds at
    least one live record that is not a known provisioned example. ``total`` is
    the sum of those stores (diagnostic); ``counts["examples"]`` reports the
    provisioned placeholders that were deliberately excluded.
    """
    counts = business_record_counts(organization_id)
    total = (
        counts["objects"] + counts["relationships"]
        + counts["leads"] + counts["suppliers"]
    )
    return {
        "organization_id": int(organization_id),
        "has_business_data": total > 0,
        "total": total,
        "counts": counts,
    }
