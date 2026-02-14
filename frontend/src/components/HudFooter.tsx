import { useEffect, useState } from 'react';

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
            <span className="hud-footer__item">
                SYS{' '}
                <span className="hud-footer__value hud-footer__value--green">
                    NOMINAL
                </span>
            </span>
            <span className="hud-footer__item">
                ARM <span className="hud-footer__value">STANDBY</span>
            </span>
            <span className="hud-footer__item">
                GRIP <span className="hud-footer__value">0.00 kPa</span>
            </span>
            <span className="hud-footer__item" id="hudClock">
                {clock}
            </span>
        </footer>
    );
}
