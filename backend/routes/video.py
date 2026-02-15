"""
Video Stream Endpoint Handler
==============================
GET /api/video/feed — Returns MJPEG stream with YOLO object detection
GET /api/detections — Returns latest detection positions as JSON
"""

from flask import Response, jsonify
from services.cv_video_service import cv_video_service


def register_video_routes(app):
    """Register video streaming endpoint routes.
    
    Parameters
    ----------
    app : Flask
        Flask application instance.
    """

    @app.route('/api/video/feed', methods=['GET'])
    def video_feed():
        """Stream processed video as MJPEG with neon detection overlays.
        
        Returns multipart JPEG stream (MJPEG) with real-time YOLO object detection.
        Video loops continuously with neon circle effects on detected objects.
        
        Returns
        -------
        Response
            Flask Response with multipart JPEG stream.
        """
        return Response(
            cv_video_service.generate_stream(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    @app.route('/api/detections', methods=['GET'])
    def detections():
        """Return the latest detection positions as JSON.
        
        Provides normalized coordinates (0-1) for detected objects,
        used by frontend for hover card positioning.
        
        Returns
        -------
        JSON
            List of detections with label, position, radius, and confidence.
        """
        return jsonify(cv_video_service.get_detections())
