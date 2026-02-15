"""
Arm/LeRobot Endpoints
======================
GET /api/arm/next — Returns the last valid pick target
"""

from flask import jsonify


def register_arm_routes(app, global_state):
    """Register arm/LeRobot interaction routes."""

    @app.route('/api/arm/next', methods=['GET'])
    def arm_next():
        """
        Return the next pick target for the arm/RL pipeline.
        When last_decision is valid, returns { "target": "<name>" }; otherwise { "target": null }.
        """
        decision = global_state.get("last_decision") or {}
        if decision.get("valid") and decision.get("target"):
            return jsonify({"target": decision["target"]})
        return jsonify({"target": None})
