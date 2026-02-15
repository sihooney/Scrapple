import { useEffect, useState } from 'react';

/**
 * HudFooter Component
 * 
 * Bottom status bar displaying system metrics and real-time clock.
 * Part of the HUD overlay system (z-index: 2).
 * 
 * Features:
 * - Fixed positioning at bottom
 * - Real-time clock (updates every second)
 * - System status indicators (SYS, ARM, GRIP)
 * - Color-coded values (green for NOMINAL, cyan for others)
 */

function useClock(): string {
    const [time, setTime] = useState(() => formatTime(new Date()));

    useEffect(() => {
        const id = setInterval(() => setTime(formatTime(new Date())), 1_000);
        return () => clearInterval(id);
    }, []);

    return time;
}

function formatTime(d: Date): string {
    return (
        String(d.getHours()).padStart(2, '0') +
        ':' +
        String(d.getMinutes()).padStart(2, '0') +
        ':' +
        String(d.getSeconds()).padStart(2, '0')
    );
}

export default function HudFooter() {
    const clock = useClock();

    return (
        <footer className="hud-footer" id="hudFooter">
            <span>
                [SYS] <span className="hud-footer__value--green">OPERATIONAL</span>
            </span>
            <span>
                [ARM] <span className="hud-footer__value">IDLE</span>
            </span>
            <span>
                [PWR] <span className="hud-footer__value--green">98.7%</span>
            </span>
            <span>
                [RAD] <span className="hud-footer__value">0.42 mSv</span>
            </span>
            <span style={{ marginLeft: 'auto' }}>
                [{clock}]
            </span>
        </footer>
    );
}
