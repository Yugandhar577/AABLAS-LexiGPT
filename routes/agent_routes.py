from flask import Blueprint, request, jsonify
from services.agent_services import plan_and_run

bp = Blueprint("agent", __name__, url_prefix="/agent")


@bp.route("/plan-run", methods=["POST"])
def plan_run():
    """
    POST JSON: { "goal": "..." }
    Returns: { plan: {...}, result: {...} }
    """
    data = request.get_json(force=True)
    goal = data.get("goal")
    if not goal:
        return jsonify({"error": "no goal provided"}), 400
    try:
        out = plan_and_run(goal)
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500