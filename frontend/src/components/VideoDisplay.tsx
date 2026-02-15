import { useEffect, useRef, useState } from 'react';

/**
 * Scrapple — Video Display Component
 * ==================================
 * Proof-of-concept webcam feed using browser camera.
 * This is a placeholder for future OpenCV-backed streaming.
 */
export default function VideoDisplay() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const startCamera = async () => {
      try {
        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error('Browser does not support webcam access.');
        }

        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user',
          },
          audio: false,
        });

        if (!isMounted) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }

        setCameraError(null);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unable to access webcam.';
        setCameraError(message);
      }
    };

    void startCamera();

    return () => {
      isMounted = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, []);

  return (
    <div className="bg-gray-950 border-2 border-cyan-500/40 rounded-lg overflow-hidden flex flex-col h-full glow-cyan">
      <div className="bg-gray-900 border-b border-cyan-500/40 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-cyan-400 font-mono font-bold uppercase tracking-wider text-sm">
            Camera Feed
          </span>
          <span className="flex items-center gap-2 bg-cyan-950 px-2 py-1 rounded text-xs text-cyan-300">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-live" />
            LIVE
          </span>
        </div>
        <span className="text-cyan-500/60 font-mono text-sm uppercase">CAM-01</span>
      </div>

      <div className="flex-1 bg-black relative overflow-hidden">
        {cameraError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <div className="text-4xl mb-4">📹</div>
            <p className="text-cyan-400 font-mono">Webcam unavailable</p>
            <small className="text-cyan-600 mt-2">{cameraError}</small>
          </div>
        ) : (
          <video
            ref={videoRef}
            className="w-full h-full object-cover"
            autoPlay
            muted
            playsInline
          />
        )}
      </div>
    </div>
  );
}