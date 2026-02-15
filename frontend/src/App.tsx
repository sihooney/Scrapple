import { useCallback, useState } from 'react';
import GridCanvas from './components/GridCanvas';
import HudHeader from './components/HudHeader';
import HudFooter from './components/HudFooter';
import CVVideoStream from './components/CVVideoStream';
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
  // ═══════════════════════════════════════════════════════════
  // STATE MANAGEMENT - PRESERVED FROM ORIGINAL
  // ═══════════════════════════════════════════════════════════
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [, setLastId] = useState(0);
  const [demoRunning, setDemoRunning] = useState(false);

  // ═══════════════════════════════════════════════════════════
  // CALLBACKS - PRESERVED FROM ORIGINAL
  // ═══════════════════════════════════════════════════════════
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

  // ═══════════════════════════════════════════════════════════
  // RENDER - ENHANCED LAYOUT WITH ALL COMPONENTS
  // ═══════════════════════════════════════════════════════════
  return (
    <div className="app-container">
      {/* ─── Background Layer (z-index: 0) ─────────────────── */}
      <GridCanvas />

      {/* ─── HUD Overlays (z-index: 2) ─────────────────────── */}
      <HudHeader />
      <HudFooter />

      {/* ─── Main Content Area (z-index: 1) ────────────────── */}
      <main className="main-content">
        {/* Left Column: Control Panels */}
        <div className="left-column">
          {/* Demo Control Panel */}
          <div className="panel demo-control-panel">
            <h2 className="panel__title">Demo Control</h2>
            <button
              type="button"
              onClick={handleStartDemo}
              disabled={demoRunning}
              className={`demo-button ${demoRunning ? 'demo-button--running' : 'demo-button--idle'}`}
            >
              {demoRunning ? '⏳ RUNNING...' : '▶ RUN ONCE'}
            </button>
            <p className="panel__status">
              {demoRunning
                ? 'Processing voice command...'
                : 'Press to run a single voice command cycle.'}
            </p>
          </div>

          {/* System Status Panel */}
          <div className="panel system-status-panel">
            <h2 className="panel__title">System Status</h2>
            <div className="status-list">
              <div className="status-item">
                <span className="status-item__label">Voice</span>
                <strong className="status-item__value status-item__value--online">ONLINE</strong>
              </div>
              <div className="status-item">
                <span className="status-item__label">Vision</span>
                <strong className="status-item__value status-item__value--online">WEBCAM</strong>
              </div>
              <div className="status-item">
                <span className="status-item__label">Arm</span>
                <strong className="status-item__value status-item__value--online">READY</strong>
              </div>
              <div className="status-item">
                <span className="status-item__label">Network</span>
                <strong className="status-item__value status-item__value--online">CONNECTED</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Video Feeds and Terminal */}
        <div className="right-column">
          {/* Video Streams Row - Side by Side */}
          <div className="video-streams-row">
            {/* CV Video Stream - YOLO Object Detection on test_video.mov */}
            <CVVideoStream />

            {/* Independent Webcam Feed - Live browser camera */}
            <VideoDisplay />
          </div>

          {/* System Log Terminal */}
          <SystemLog logs={logs} />
        </div>
      </main>
    </div>
  );
}
