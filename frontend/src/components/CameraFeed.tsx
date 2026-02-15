/**
 * CameraFeed Component
 * 
 * LeRobot Camera Placeholder - Static component that will be replaced with actual LeRobot camera feed.
 * This is a visual placeholder showing "NO SIGNAL" until the LeRobot camera integration is complete.
 * 
 * Features:
 * - Corner brackets for HUD-style framing
 * - Crosshair overlay
 * - Blinking "NO SIGNAL" indicator
 * - Scanline effect (via CSS)
 */
export default function CameraFeed() {
    return (
        <div className="camera-feed" id="cameraFeed">
            <div className="camera-feed__corner camera-feed__corner--tl" />
            <div className="camera-feed__corner camera-feed__corner--tr" />
            <div className="camera-feed__corner camera-feed__corner--bl" />
            <div className="camera-feed__corner camera-feed__corner--br" />

            <span className="camera-feed__label camera-feed__label--top">
                LIVE FEED — ARM CAM 01
            </span>

            <div className="camera-feed__crosshair" />

            <span className="camera-feed__label camera-feed__label--bottom">
                NO SIGNAL
            </span>
        </div>
    );
}
