from app.communication.models import MessageProposal
from app import db


def test_proposal_created(app):
    with app.app_context():
        proposal = MessageProposal(to="9999999999", message="hi")
        db.session.add(proposal)
        db.session.flush()
        assert proposal.status == "pending"