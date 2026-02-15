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
        <footer
            className="bg-gray-950 border-t-2 border-cyan-500/40 px-6 py-3 flex justify-between items-center text-xs font-mono glow-cyan"
            id="hudFooter"
        >
            <span className="text-cyan-300 uppercase">
                SYS{' '}
                <span className="text-emerald-400 font-bold">
                    NOMINAL
                </span>
            </span>
            <span className="text-cyan-300 uppercase">
                ARM <span className="text-cyan-200">STANDBY</span>
            </span>
            <span className="text-cyan-300 uppercase">
                GRIP <span className="text-cyan-200">0.00 kPa</span>
            </span>
            <span className="text-cyan-200 uppercase font-bold" id="hudClock">
                {clock}
            </span>
        </footer>
    );
}
