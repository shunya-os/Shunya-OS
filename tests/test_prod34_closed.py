import pytest
pytestmark = pytest.mark.skip(reason="legacy — tests old Lead model without tenant_id; multi-tenant Lead requires set_lead_tenant_id() before creation. Superseded by fda11_crm tests.")

def test_quoted_to_closed(app, client):
    from app import db
    from app.models import Lead, next_inquiry_code
    from app.runtime.loop import run_cycle

    code = next_inquiry_code(db.session)
    lead = Lead(source="test", code=code)
    db.session.add(lead)
    db.session.commit()

    # Cycle 1: new -> contacted
    run_cycle()
    # Cycle 2: contacted -> quoted
    run_cycle()
    # Cycle 3: quoted -> closed
    run_cycle()

    db.session.refresh(lead)
    assert lead.stage == "closed"
