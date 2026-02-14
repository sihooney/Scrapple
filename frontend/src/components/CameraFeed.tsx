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
