from app import db
from app.objects.models import Object

class ObjectService:

    @staticmethod
    def create_object(object_type: str, state: dict = None):
        obj = Object(
            object_type=object_type,
            state=state or {},
        )

        db.session.add(obj)
        db.session.commit()

        return obj

    @staticmethod
    def update_state(obj: Object, new_state: dict):
        obj.state = {**(obj.state or {}), **new_state}
        db.session.commit()
        return obj
