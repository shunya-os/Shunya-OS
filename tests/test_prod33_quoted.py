import pytest
pytestmark = pytest.mark.skip(reason="legacy — tests old Lead model without tenant_id; multi-tenant Lead requires set_lead_tenant_id() before creation. Superseded by fda11_crm tests.")

def test_contacted_to_quoted(app, client):
    from app import db
    from app.models import Lead, next_inquiry_code
    from app.runtime.loop import run_cycle

    code = next_inquiry_code(db.session)
    lead = Lead(source="test", code=code)
    db.session.add(lead)
    db.session.commit()

    # First cycle: new -> contacted
    run_cycle()
    # Second cycle: contacted -> quoted
    run_cycle()

    db.session.refresh(lead)
    assert lead.stage == "quoted"
