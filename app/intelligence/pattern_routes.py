from flask import Blueprint, jsonify
from app.objects.models import Object
from app.intelligence.engine import IntelligenceEngine

pattern_bp = Blueprint("patterns", __name__, url_prefix="/api/v1/patterns")

@pattern_bp.route("/<int:object_id>/suggest", methods=["GET"])
def suggest(object_id):
    obj = Object.query.get_or_404(object_id)
    result = IntelligenceEngine.suggest(obj)
    return jsonify(result)