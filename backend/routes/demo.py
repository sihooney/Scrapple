"""
Demo Control Endpoints
=======================
POST /api/demo/start — Signal demo loop started
POST /api/demo/stop  — Signal demo loop stopped
"""

from flask import jsonify


def register_demo_routes(app, global_state):
    """Register demo control routes."""

    @app.route('/api/demo/start', methods=['POST'])
    def demo_start():
        """Signal that the demo loop has started (frontend Start button)."""
        global_state["demo_running"] = True
        return jsonify({"ok": True, "demo_running": True})

    @app.route('/api/demo/stop', methods=['POST'])
    def demo_stop():
        """Signal that the demo loop has stopped (frontend Stop button)."""
        global_state["demo_running"] = False
        return jsonify({"ok": True, "demo_running": False})
