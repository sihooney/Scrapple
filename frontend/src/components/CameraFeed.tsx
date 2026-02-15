export default function CameraFeed() {
    return (
        <div className="relative w-full h-full border-4 border-cyan-500/60" id="cameraFeed">
            {/* Corner brackets */}
            <div
                className="absolute top-0 left-0 w-6 h-6 border-t-4 border-l-4 border-cyan-400"
                style={{ transform: 'translate(-2px, -2px)' }}
            />
            <div
                className="absolute top-0 right-0 w-6 h-6 border-t-4 border-r-4 border-cyan-400"
                style={{ transform: 'translate(2px, -2px)' }}
            />
            <div
                className="absolute bottom-0 left-0 w-6 h-6 border-b-4 border-l-4 border-cyan-400"
                style={{ transform: 'translate(-2px, 2px)' }}
            />
            <div
                className="absolute bottom-0 right-0 w-6 h-6 border-b-4 border-r-4 border-cyan-400"
                style={{ transform: 'translate(2px, 2px)' }}
            />

            {/* Top label */}
            <span className="absolute top-3 left-1/2 -translate-x-1/2 bg-gray-950 px-3 py-1 font-mono text-xs uppercase text-cyan-300 border border-cyan-500/40 whitespace-nowrap">
                LIVE FEED — ARM CAM 01
            </span>

            {/* Crosshair */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="relative w-16 h-16">
                    <div className="absolute inset-0 border border-cyan-500/30" />
                    <div className="absolute top-1/2 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent" />
                    <div className="absolute top-0 bottom-0 left-1/2 w-px bg-gradient-to-b from-transparent via-cyan-500/40 to-transparent" />
                    <div className="absolute top-1/2 left-1/2 w-1 h-1 -translate-x-1/2 -translate-y-1/2 bg-cyan-500/60 rounded-full" />
                </div>
            </div>

            {/* Bottom label */}
            <span className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-gray-950 px-3 py-1 font-mono text-xs uppercase text-red-400 border border-red-500/40">
                NO SIGNAL
            </span>
        </div>
    );
}
