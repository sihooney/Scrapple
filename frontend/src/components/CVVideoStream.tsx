import { useEffect, useRef, useState, useCallback } from 'react';

const ICON_MAP: Record<string, string> = {
  hotdog: '🌭',
  skull: '💀',
  nut: '🔩',
  gear: '⚙️',
  heart: '❤️',
};

const API_BASE = 'http://localhost:5000';

interface Detection {
  label: string;
  cx: number;
  cy: number;
  radius: number;
  confidence: number;
}

interface CVVideoStreamProps {
  streamUrl: string;
  label: string;
  showDetections?: boolean;
  onPickTarget?: (target: string) => void;
}

export default function CVVideoStream({ 
  streamUrl, 
  label, 
  showDetections = false,
  onPickTarget 
}: CVVideoStreamProps) {
  const [hasSignal, setHasSignal] = useState(false);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [hovered, setHovered] = useState<number | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [imgRect, setImgRect] = useState({ x: 0, y: 0, w: 0, h: 0 });

  const updateImgRect = useCallback(() => {
    const img = imgRef.current;
    const container = containerRef.current;
    if (!img || !container || !img.naturalWidth) return;

    const containerRect = container.getBoundingClientRect();
    const cw = containerRect.width;
    const ch = containerRect.height;
    const nw = img.naturalWidth;
    const nh = img.naturalHeight;

    const scale = Math.min(cw / nw, ch / nh);
    const renderedW = nw * scale;
    const renderedH = nh * scale;
    const offsetX = (cw - renderedW) / 2;
    const offsetY = (ch - renderedH) / 2;

    setImgRect({ x: offsetX, y: offsetY, w: renderedW, h: renderedH });
  }, []);

  // Poll detections (only if showDetections is true)
  useEffect(() => {
    if (!showDetections) return;
    
    let isMounted = true;
    
    const pollDetections = async () => {
      if (!isMounted) return;
      try {
        const res = await fetch(`${API_BASE}/api/detections`);
        if (res.ok && isMounted) {
          const data: Detection[] = await res.json();
          setDetections(data);
        }
      } catch {
        // backend not ready
      }
    };
    
    const interval = setInterval(pollDetections, 500);
    pollDetections();
    
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [showDetections]);

  useEffect(() => {
    updateImgRect();
    window.addEventListener('resize', updateImgRect);
    return () => window.removeEventListener('resize', updateImgRect);
  }, [updateImgRect]);

  const toPixel = (det: Detection) => {
    const px = imgRect.x + det.cx * imgRect.w;
    const py = imgRect.y + det.cy * imgRect.h;
    const pr = det.radius * Math.max(imgRect.w, imgRect.h);
    return { px, py, pr };
  };

  return (
    <div className="cv-video-stream" ref={containerRef}>
      <div className="cv-video-stream__corner cv-video-stream__corner--tl" />
      <div className="cv-video-stream__corner cv-video-stream__corner--tr" />
      <div className="cv-video-stream__corner cv-video-stream__corner--bl" />
      <div className="cv-video-stream__corner cv-video-stream__corner--br" />

      <span className="cv-video-stream__label cv-video-stream__label--top">
        [{label}] {showDetections ? 'YOLO' : 'RAW'}
      </span>

      <img
        ref={imgRef}
        className="cv-video-stream__stream"
        src={streamUrl}
        alt={`${label} feed`}
        onLoad={() => {
          setHasSignal(true);
          updateImgRect();
        }}
        onError={() => setHasSignal(false)}
      />

      {/* Detection overlays (only for YOLO stream) */}
      {showDetections && hasSignal &&
        detections.map((det, i) => {
          const { px, py, pr } = toPixel(det);
          const isHovered = hovered === i;
          const zoneSize = pr * 2 + 20;

          return (
            <div
              key={`${det.label}-${i}`}
              className="detection-zone"
              style={{
                left: px - zoneSize / 2,
                top: py - zoneSize / 2,
                width: zoneSize,
                height: zoneSize,
              }}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
            >
              {isHovered && (
                <div className="detection-card">
                  <span className="detection-card__icon-emoji">
                    {ICON_MAP[det.label] || '📦'}
                  </span>
                  <span className="detection-card__label">{det.label.toUpperCase()}</span>
                  <span className="detection-card__conf">
                    {(det.confidence * 100).toFixed(0)}%
                  </span>
                  <button 
                    className="detection-card__btn"
                    onClick={async (e) => {
                      e.stopPropagation();
                      try {
                        await fetch(`${API_BASE}/api/lerobot/run`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                        });
                        onPickTarget?.(det.label);
                      } catch (err) {
                        console.error('[CV] Failed to trigger LeRobot:', err);
                      }
                    }}
                  >
                    [ACQUIRE]
                  </button>
                </div>
              )}
            </div>
          );
        })}

      {hasSignal && <div className="cv-video-stream__crosshair cv-video-stream__crosshair--overlay" />}

      <span className="cv-video-stream__label cv-video-stream__label--bottom">
        {hasSignal ? 'ACTIVE' : 'NO_SIGNAL'}
      </span>
    </div>
  );
}
