from flask import Blueprint, jsonify
from app.objects.models import Object
from app.execution_engine.engine import ExecutionEngine

execution_bp = Blueprint("execution_engine", __name__, url_prefix="/api/v1/execution")

@execution_bp.route("/<int:object_id>/run", methods=["POST"])
def run_execution(object_id):
    obj = Object.query.get_or_404(object_id)

    result = ExecutionEngine.execute(obj)

    return jsonify(result)