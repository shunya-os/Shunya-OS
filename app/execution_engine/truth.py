from app.objects.models import Object
from app import db

class TruthService:

    @staticmethod
    def apply_truth(obj: Object, updates: dict):
        obj.state = {**(obj.state or {}), **updates}
        db.session.commit()
        return obj