import { useEffect, useRef, useState, useCallback } from 'react';

import gearIcon from '../icons/gear.png';
import heartIcon from '../icons/heart.png';
import hotdogIcon from '../icons/hotdog.png';
import nutIcon from '../icons/nut.png';
import skullIcon from '../icons/skull.png';

const ICON_MAP: Record<string, string> = {
  hotdog: hotdogIcon,
  skull: skullIcon,
  nut: nutIcon,
  gear: gearIcon,
  heart: heartIcon,
};

interface Detection {
  label: string;
  cx: number; // 0-1 normalized
  cy: number;
  radius: number;
  confidence: number;
}

export default function CVVideoStream() {
  const [hasSignal, setHasSignal] = useState(false);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [hovered, setHovered] = useState<number | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [imgRect, setImgRect] = useState({ x: 0, y: 0, w: 0, h: 0 });

  // Calculate the actual rendered area of the <img> (accounting for object-fit: contain)
  const updateImgRect = useCallback(() => {
    const img = imgRef.current;
    const container = containerRef.current;
    if (!img || !container || !img.naturalWidth) return;

    const containerRect = container.getBoundingClientRect();
    const cw = containerRect.width;
    const ch = containerRect.height;
    const nw = img.naturalWidth;
    const nh = img.naturalHeight;

    // object-fit: contain math
    const scale = Math.min(cw / nw, ch / nh);
    const renderedW = nw * scale;
    const renderedH = nh * scale;
    const offsetX = (cw - renderedW) / 2;
    const offsetY = (ch - renderedH) / 2;

    setImgRect({ x: offsetX, y: offsetY, w: renderedW, h: renderedH });
  }, []);

  // Poll detections from backend
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch('http://localhost:5000/api/detections');
        if (res.ok) {
          const data: Detection[] = await res.json();
          setDetections(data);
        }
      } catch {
        // backend not ready yet
      }
    }, 200);
    return () => clearInterval(interval);
  }, []);

  // Update image rect on resize
  useEffect(() => {
    updateImgRect();
    window.addEventListener('resize', updateImgRect);
    return () => window.removeEventListener('resize', updateImgRect);
  }, [updateImgRect]);

  // Map normalized detection to pixel position within the container
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
        LIVE FEED — ARM CAM 01
      </span>

      {/* MJPEG stream from Flask backend */}
      <img
        ref={imgRef}
        className="cv-video-stream__stream"
        src="http://localhost:5000/api/video/feed"
        alt="Live detection feed"
        onLoad={() => {
          setHasSignal(true);
          updateImgRect();
        }}
        onError={() => setHasSignal(false)}
      />

      {/* Detection hit zones + hover cards */}
      {hasSignal &&
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
                  <img
                    className="detection-card__icon"
                    src={ICON_MAP[det.label] || ''}
                    alt={det.label}
                  />
                  <span className="detection-card__label">{det.label.toUpperCase()}</span>
                  <span className="detection-card__conf">
                    {(det.confidence * 100).toFixed(0)}% MATCH
                  </span>
                  <button className="detection-card__btn">PICK UP</button>
                </div>
              )}
            </div>
          );
        })}

      {/* Crosshair overlay */}
      {hasSignal && <div className="cv-video-stream__crosshair cv-video-stream__crosshair--overlay" />}

      <span className="cv-video-stream__label cv-video-stream__label--bottom">
        {hasSignal ? 'DETECTING' : 'NO SIGNAL'}
      </span>
    </div>
  );
}
