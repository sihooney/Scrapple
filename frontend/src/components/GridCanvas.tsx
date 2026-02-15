import { useEffect, useRef } from 'react';

/**
 * GridCanvas Component
 * 
 * Animated background layer with jittered grid lines and horizontal scanning beams.
 * Provides the cyberpunk HUD aesthetic for the dashboard.
 * 
 * Features:
 * - Jittered grid pattern for visual interest
 * - Animated horizontal scanning beams
 * - 60fps animation using requestAnimationFrame
 * - Responsive to window resize
 * - z-index: 0 (background layer)
 */

/* ── Tunables (OPTIMIZED for performance) ─────────────────── */
const GRID_BASE_SPACING = 60;  // Larger spacing = fewer lines
const GRID_JITTER = 8;
const GRID_LINE_COLOR = 'rgba(0, 255, 65, 0.04)';  // Match new theme
const BEAM_COLOR_CORE = 'rgba(0, 255, 65, 0.7)';
const BEAM_COLOR_GLOW = 'rgba(0, 255, 65, 0.15)';
const BEAM_TRAIL_MIN = 40;  // Shorter trails
const BEAM_TRAIL_MAX = 100;
const BEAM_SPEED_MIN = 3;
const BEAM_SPEED_MAX = 6;
const BEAM_SPAWN_RATE = 0.03;  // Much lower spawn rate
const MAX_BEAMS = 15;  // Much fewer beams
const TARGET_FPS = 20;  // Reduced from 60fps to 20fps

/* ── Helpers ───────────────────────────────────────────────── */
const rand = (lo: number, hi: number) => lo + Math.random() * (hi - lo);

/* ── Types ─────────────────────────────────────────────────── */
interface Beam {
    x: number;
    y: number;
    speed: number;
    trail: number;
    dead: boolean;
    opacity: number;
}

function createBeam(y: number): Beam {
    return {
        x: -rand(BEAM_TRAIL_MIN, BEAM_TRAIL_MAX),
        y,
        speed: rand(BEAM_SPEED_MIN, BEAM_SPEED_MAX),
        trail: rand(BEAM_TRAIL_MIN, BEAM_TRAIL_MAX),
        dead: false,
        opacity: rand(0.5, 1),
    };
}

/* ── Update beam (straight left→right, passes behind rect via z-index) */
function updateBeam(b: Beam, W: number) {
    b.x += b.speed;
    if (b.x - b.trail > W) b.dead = true;
}

/* ── Draw beam ─────────────────────────────────────────────── */
function drawBeam(ctx: CanvasRenderingContext2D, b: Beam) {
    const x2 = b.x;
    const x1 = b.x - b.trail;

    const grad = ctx.createLinearGradient(x1, b.y, x2, b.y);
    grad.addColorStop(0, 'transparent');
    grad.addColorStop(0.6, BEAM_COLOR_GLOW);
    grad.addColorStop(1, BEAM_COLOR_CORE);

    ctx.save();
    ctx.globalAlpha = b.opacity;

    // Wide glow
    ctx.strokeStyle = grad;
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(x1, b.y);
    ctx.lineTo(x2, b.y);
    ctx.stroke();

    // Core line
    ctx.strokeStyle = BEAM_COLOR_CORE;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(x1 + b.trail * 0.4, b.y);
    ctx.lineTo(x2, b.y);
    ctx.stroke();

    // Leading dot
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(x2, b.y, 1.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
}

/* ── Component ─────────────────────────────────────────────── */

export default function GridCanvas() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let W = 0;
        let H = 0;
        let gridLinesY: number[] = [];
        let gridLinesX: number[] = [];
        const beams: Beam[] = [];
        let animId = 0;

        /* ── sizing ─────────────────────────────────────────── */
        function resize() {
            const dpr = window.devicePixelRatio || 1;
            W = window.innerWidth;
            H = window.innerHeight;
            canvas!.width = W * dpr;
            canvas!.height = H * dpr;
            canvas!.style.width = W + 'px';
            canvas!.style.height = H + 'px';
            ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);

            buildGrid();
        }

        function buildGrid() {
            gridLinesY = [];
            gridLinesX = [];
            for (let y = GRID_BASE_SPACING; y < H; y += GRID_BASE_SPACING) {
                gridLinesY.push(y + rand(-GRID_JITTER, GRID_JITTER));
            }
            for (let x = GRID_BASE_SPACING; x < W; x += GRID_BASE_SPACING) {
                gridLinesX.push(x + rand(-GRID_JITTER, GRID_JITTER));
            }
        }

        /* ── grid drawing ───────────────────────────────────── */
        function drawGrid() {
            ctx!.strokeStyle = GRID_LINE_COLOR;
            ctx!.lineWidth = 0.5;
            ctx!.beginPath();
            for (const y of gridLinesY) {
                ctx!.moveTo(0, y);
                ctx!.lineTo(W, y);
            }
            for (const x of gridLinesX) {
                ctx!.moveTo(x, 0);
                ctx!.lineTo(x, H);
            }
            ctx!.stroke();
        }

        /* ── spawning ───────────────────────────────────────── */
        function spawnBeams() {
            if (beams.length >= MAX_BEAMS) return;
            for (const y of gridLinesY) {
                if (Math.random() < BEAM_SPAWN_RATE / 60) {
                    beams.push(createBeam(y));
                }
            }
        }

        /* ── frame loop (throttled to TARGET_FPS) ────────────── */
        let lastFrameTime = 0;
        const frameInterval = 1000 / TARGET_FPS;
        
        function frame(currentTime: number) {
            animId = requestAnimationFrame(frame);
            
            // Throttle frame rate
            const elapsed = currentTime - lastFrameTime;
            if (elapsed < frameInterval) return;
            lastFrameTime = currentTime - (elapsed % frameInterval);
            
            ctx!.clearRect(0, 0, W, H);
            drawGrid();
            spawnBeams();

            for (let i = beams.length - 1; i >= 0; i--) {
                updateBeam(beams[i], W);
                if (beams[i].dead) {
                    beams.splice(i, 1);
                } else {
                    drawBeam(ctx!, beams[i]);
                }
            }
        }

        /* ── init ───────────────────────────────────────────── */
        resize();
        window.addEventListener('resize', resize);
        animId = requestAnimationFrame((t) => frame(t));

        return () => {
            window.removeEventListener('resize', resize);
            cancelAnimationFrame(animId);
        };
    }, []);

    return <canvas ref={canvasRef} className="grid-canvas" />;
}
