"""Seed HR & People entity types for Shunya OS.

Run as script:
    python3 seed_scripts/seed_hr.py

This adds HR entity types (employee, department, leave_request, etc.)
to all active tenants.  Functions are importable without a DB connection
(for use in tests or seed_all.py).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("FLASK_ENV", "development")

from app.shunya.hr import HR_ENTITY_TYPES


def seed_hr_for_tenant(tenant_id: int) -> int:
    """Add HR entity definitions for a tenant.  Returns count created.

    Caller must be inside a Flask app context with initialized DB.
    """
    from app import db
    from app.models import EntityDefinition

    created = 0
    for etype, config in HR_ENTITY_TYPES.items():
        existing = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=etype
        ).first()
        if existing:
            continue

        definition = EntityDefinition(
            tenant_id=tenant_id,
            type=etype,
            label=config["label"],
            label_plural=f"{config['label']}s",
            icon=config["icon"],
            schema=config["schema"],
            statuses=config["statuses"],
            layout=config.get("layout", "table"),
            searchable_fields=config.get("searchable_fields", []),
            primary_field=config["schema"][0]["name"] if config["schema"] else "name",
        )
        db.session.add(definition)
        created += 1

    db.session.commit()
    return created


def seed_all_tenants() -> int:
    """Seed HR entity types for all active tenants.  Returns total created.

    Caller must be inside a Flask app context.
    """
    from app import db
    from app.models import Tenant

    tenants = db.session.query(Tenant).filter_by(is_active=True).all()
    total = 0
    for tenant in tenants:
        n = seed_hr_for_tenant(tenant.id)
        if n:
            print(f"  {tenant.company_name}: {n} HR entity types created")
        total += n
    return total


if __name__ == "__main__":
    from app import create_app, db

    app = create_app("development")
    with app.app_context():
        db.create_all()
        print("Seeding HR entity types...")
        total = seed_all_tenants()
        print(f"✅ Done! Created {total} HR entity definition(s) across all tenants.")