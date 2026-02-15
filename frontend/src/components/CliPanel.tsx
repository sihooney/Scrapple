import { useCallback, useEffect, useRef, useState } from 'react';

interface LogEntry {
    id: number;
    role: 'system' | 'user' | 'bot';
    text: string;
}

const ROLE_PREFIX: Record<string, string> = {
    system: '[SYS]',
    user: '[YOU]',
    bot: '[BOT]',
};

export default function CliPanel() {
    const [entries, setEntries] = useState<LogEntry[]>([]);
    const [busy, setBusy] = useState(false);
    const logRef = useRef<HTMLDivElement>(null);
    const idRef = useRef(0);

    // Auto-scroll to bottom when new entries arrive
    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [entries]);

    const addEntry = useCallback((role: string, text: string) => {
        idRef.current += 1;
        const entry: LogEntry = {
            id: idRef.current,
            role: role as LogEntry['role'],
            text,
        };
        setEntries(prev => [...prev, entry]);
    }, []);

    const post = async (url: string, body?: object) => {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body ? JSON.stringify(body) : undefined,
        });
        return res.json();
    };

    const handleVoice = useCallback(async () => {
        if (busy) return;
        setBusy(true);

        try {
            // ── Step 1: Announce objects (TTS plays on server) ───────
            addEntry('system', 'Initiating voice scan...');
            const startData = await post('/api/voice/start');

            if (startData.error) {
                addEntry('system', `Error: ${startData.error}`);
                setBusy(false);
                return;
            }

            if (!startData.prompt) {
                addEntry('system', startData.message || 'No objects detected.');
                setBusy(false);
                return;
            }

            addEntry('bot', startData.prompt);

            if (startData.tts_error) {
                addEntry('system', `TTS: ${startData.tts_error}`);
            }

            // ── Step 2: Record & transcribe (mic captures on server) ─
            addEntry('system', '🎙️ Listening...');
            const recData = await post('/api/voice/record', { duration: 4 });

            if (recData.error) {
                addEntry('system', `Error: ${recData.error}`);
                setBusy(false);
                return;
            }

            if (!recData.transcript) {
                addEntry('system', 'No speech detected.');
                setBusy(false);
                return;
            }

            addEntry('user', recData.transcript);

            // ── Step 3: Evaluate with Gemini & speak result ──────────
            addEntry('system', 'Evaluating with Gemini...');
            const evalData = await post('/api/voice/evaluate', {
                command: recData.transcript,
                objects: startData.objects,
            });

            if (evalData.error) {
                addEntry('system', `Error: ${evalData.error}`);
                setBusy(false);
                return;
            }

            const decision = evalData.decision;
            const valid = decision?.valid;
            addEntry('system', `Decision: ${valid ? '✅ VALID' : '❌ INVALID'} — ${decision?.reason || ''}`);
            addEntry('bot', evalData.response);

        } catch (err) {
            addEntry('system',
                `Connection failed: ${err instanceof Error ? err.message : String(err)}`
            );
        }

        setBusy(false);
    }, [busy, addEntry]);

    return (
        <div className="cli-panel" id="cliPanel">
            <div className="cli-panel__header">
                <span className="cli-panel__title">COMMAND TERMINAL</span>
                <button
                    type="button"
                    className={`cli-panel__voice-btn ${busy ? 'cli-panel__voice-btn--listening' : ''}`}
                    disabled={busy}
                    onClick={handleVoice}
                >
                    {busy ? '● LISTENING...' : '🎙️ VOICE MODE'}
                </button>
            </div>

            <div className="cli-panel__log" ref={logRef}>
                {entries.length === 0 ? (
                    <span className="cli-panel__empty">
                        Press VOICE MODE to begin salvage target selection
                    </span>
                ) : (
                    entries.map(e => (
                        <div key={e.id} className={`cli-panel__entry cli-panel__entry--${e.role}`}>
                            <span className="cli-panel__prefix">{ROLE_PREFIX[e.role]}</span>
                            {e.text}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
