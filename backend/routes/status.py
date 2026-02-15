"""
Status Endpoint Handler
=======================
GET /api/status — Returns system status and current state
"""

from flask import jsonify


def register_status_routes(app, global_state):
    """Register status endpoint routes."""

    @app.route('/api/status', methods=['GET'])
    def status():
        """Return system status and current state."""
        return jsonify({"status": "online", "state": global_state})
