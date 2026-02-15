import { useCallback, useRef, useState } from 'react';
import SystemLog from './components/SystemLog';
import VideoDisplay from './components/VideoDisplay';

const API_BASE = 'http://localhost:5000';

interface LogEntry {
  id: number;
  type: 'user' | 'bot' | 'system';
  text: string;
  timestamp: string;
}

export default function App() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [lastId, setLastId] = useState(0);
  const [demoRunning, setDemoRunning] = useState(false);
  const demoRunningRef = useRef(false);

  const addLog = useCallback((type: LogEntry['type'], text: string) => {
    const timestamp = new Date().toLocaleTimeString([], {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });

    setLastId((prev) => {
      const newId = prev + 1;
      setLogs((prevLogs) => [...prevLogs, { id: newId, type, text, timestamp }]);
      return newId;
    });
  }, []);

  const handleVoiceResult = useCallback(
    (data: Record<string, unknown>) => {
      if (data.prompt_spoken) {
        addLog('bot', String(data.prompt_spoken));
      }

      if (data.error) {
        addLog('system', `Error: ${String(data.error)}`);
        if (data.tts_result) addLog('bot', String(data.tts_result));
        return;
      }

      if (data.command) {
        addLog('system', `🎤 Speech detected: "${String(data.command)}"`);
        addLog('user', `"${String(data.command)}"`);
      } else {
        addLog('system', '🎤 No speech detected');
      }

      if (data.tts_result) {
        addLog('bot', String(data.tts_result));
      }

      if (data.decision && typeof data.decision === 'object') {
        const d = data.decision as { valid?: boolean; reason?: string; target?: string | null };
        if (d.valid) {
          addLog('system', `✅ ACCEPTED: ${d.reason ?? ''}`);
          if (d.target) {
            addLog('system', `🤖 LeRobot: pick "${d.target}"`);
          }
        } else {
          addLog('system', `❌ REJECTED: ${d.reason ?? ''}`);
        }
      }
    },
    [addLog]
  );

  const handleStartDemo = useCallback(async () => {
    if (demoRunning) return;

    setDemoRunning(true);
    addLog('system', '▶ Running voice command...');

    try {
      const res = await fetch(`${API_BASE}/api/voice/listen`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: 4 }),
      });

      const data = await res.json();
      handleVoiceResult(data);

      if (!res.ok) {
        addLog('system', `Request failed: ${res.status}`);
      }
    } catch (err) {
      addLog('system', `Connection error: ${err instanceof Error ? err.message : String(err)}`);
    }

    setDemoRunning(false);
    addLog('system', '■ Command complete');
  }, [demoRunning, addLog, handleVoiceResult]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black flex flex-col">
      {/* Grid overlay background */}
      <div
        className="fixed inset-0 opacity-5 pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(0deg, transparent 24%, rgba(0, 255, 255, 0.05) 25%, rgba(0, 255, 255, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, 0.05) 75%, rgba(0, 255, 255, 0.05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(0, 255, 255, 0.05) 25%, rgba(0, 255, 255, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, 0.05) 75%, rgba(0, 255, 255, 0.05) 76%, transparent 77%, transparent)',
          backgroundSize: '50px 50px',
        }}
        aria-hidden="true"
      />

      <div className="relative flex flex-col h-screen">
        {/* Header */}
        <header className="bg-gray-950 border-b border-cyan-500/40 px-8 py-6 glow-cyan flex items-center justify-between">
          <div>
            <p className="text-xs uppercase text-cyan-500 tracking-widest font-mono">MakeUofT 2026</p>
            <h1 className="text-3xl font-bold text-cyan-300 uppercase tracking-wider mt-1">
              Scrapple Control Console
            </h1>
            <p className="text-sm text-cyan-500/70 mt-2 font-mono">
              Voice-driven salvage loop with live camera proof-of-concept.
            </p>
          </div>

          <div
            className={`px-4 py-2 border-2 font-mono font-bold text-sm transition-all ${
              demoRunning
                ? 'bg-red-950/50 border-red-500 text-red-400 shadow-lg shadow-red-500/30'
                : 'bg-gray-800/50 border-cyan-500/40 text-cyan-400'
            }`}
          >
            {demoRunning ? '● ACTIVE' : '○ IDLE'}
          </div>
        </header>

        {/* Main Grid */}
        <main className="flex-1 overflow-hidden grid grid-cols-3 gap-4 p-4">
          {/* Left column */}
          <section className="col-span-1 space-y-4 overflow-auto scrollbar-hide">
            {/* Demo Control Panel */}
            <div className="bg-gray-950 border-2 border-cyan-500/40 rounded-lg p-5 glow-cyan">
              <h2 className="text-lg font-bold text-cyan-400 uppercase tracking-wider mb-4">
                Demo Control
              </h2>
              <button
                type="button"
                onClick={handleStartDemo}
                disabled={demoRunning}
                className={`w-full py-3 px-4 font-mono font-bold uppercase tracking-widest transition-all ${
                  demoRunning
                    ? 'bg-gray-700 border-2 border-gray-500 text-gray-400 cursor-not-allowed'
                    : 'bg-emerald-900/50 border-2 border-emerald-500 text-emerald-300 hover:bg-emerald-900/70'
                }`}
              >
                {demoRunning ? '⏳ RUNNING...' : '▶ RUN ONCE'}
              </button>

              <p className="text-xs text-cyan-500/70 mt-4 font-mono">
                {demoRunning
                  ? 'Processing voice command...'
                  : 'Press to run a single voice command cycle.'}
              </p>
            </div>

            {/* System Status Panel */}
            <div className="bg-gray-950 border-2 border-cyan-500/40 rounded-lg p-5 glow-cyan flex-1">
              <h2 className="text-lg font-bold text-cyan-400 uppercase tracking-wider mb-4">
                System Status
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between text-sm font-mono border-b border-cyan-500/20 pb-2">
                  <span className="text-cyan-500">Voice</span>
                  <strong className="text-emerald-400">ONLINE</strong>
                </div>
                <div className="flex justify-between text-sm font-mono border-b border-cyan-500/20 pb-2">
                  <span className="text-cyan-500">Vision</span>
                  <strong className="text-emerald-400">WEBCAM</strong>
                </div>
                <div className="flex justify-between text-sm font-mono border-b border-cyan-500/20 pb-2">
                  <span className="text-cyan-500">Arm</span>
                  <strong className="text-emerald-400">READY</strong>
                </div>
                <div className="flex justify-between text-sm font-mono pb-2">
                  <span className="text-cyan-500">Network</span>
                  <strong className="text-emerald-400">CONNECTED</strong>
                </div>
              </div>
            </div>
          </section>

          {/* Right column */}
          <section className="col-span-2 space-y-4 overflow-hidden grid grid-rows-2">
            <div>
              <VideoDisplay />
            </div>
            <div>
              <SystemLog logs={logs} />
            </div>
          </section>
        </main>

        {/* Footer */}
        <footer className="bg-gray-950 border-t border-cyan-500/40 px-8 py-3 flex justify-between text-xs font-mono text-cyan-500/60">
          <span>Scrapple • Salvage Robot Frontend</span>
          <span>Backend: {API_BASE}</span>
        </footer>
      </div>
    </div>
  );
}