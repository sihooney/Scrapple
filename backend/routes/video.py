"""
Video Stream Endpoint Handler
==============================
GET /api/video/feed     — MJPEG stream with YOLO detection (camera 2 - front)
GET /api/video/handeye  — MJPEG stream raw feed (camera 3 - handeye)
GET /api/detections     — Latest detection positions as JSON
"""

from flask import Response, jsonify
from services.cv_video_service import cv_video_service


def register_video_routes(app):
    """Register video streaming endpoint routes."""

    @app.route('/api/video/feed', methods=['GET'])
    def video_feed():
        """Stream front camera (index 2) as MJPEG with YOLO detection overlays."""
        return Response(
            cv_video_service.generate_stream(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    @app.route('/api/video/handeye', methods=['GET'])
    def video_handeye():
        """Stream handeye camera (index 3) as raw MJPEG feed."""
        return Response(
            cv_video_service.generate_stream_handeye(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    @app.route('/api/detections', methods=['GET'])
    def detections():
        """Return the latest detection positions as JSON."""
        return jsonify(cv_video_service.get_detections())
