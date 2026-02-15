import { useCallback, useState, useEffect } from 'react';
import GridCanvas from './components/GridCanvas';
import HudHeader from './components/HudHeader';
import HudFooter from './components/HudFooter';
import CVVideoStream from './components/CVVideoStream';
import SystemLog from './components/SystemLog';
import VoiceControl from './components/VoiceControl';

const API_BASE = 'http://localhost:5000';

interface LogEntry {
  id: number;
  type: 'user' | 'bot' | 'system';
  text: string;
  timestamp: string;
}

interface LeRobotStatus {
  running: boolean;
  last_target: string | null;
}

export default function App() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [, setLastId] = useState(0);
  const [lerobotStatus, setLerobotStatus] = useState<LeRobotStatus>({ running: false, last_target: null });

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

  // Poll LeRobot status (every 5 seconds)
  useEffect(() => {
    let isMounted = true;
    
    const pollStatus = async () => {
      if (!isMounted) return;
      try {
        const res = await fetch(`${API_BASE}/api/lerobot/status`);
        if (res.ok && isMounted) {
          const data: LeRobotStatus = await res.json();
          setLerobotStatus(data);
        }
      } catch {
        // Backend not ready
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handlePickTarget = useCallback((target: string) => {
    addLog('system', `🎯 CV Pick triggered: "${target}"`);
  }, [addLog]);

  return (
    <div className="app-container">
      <GridCanvas />
      <HudHeader />
      <HudFooter />

      <main className="main-content">
        {/* Left Column: Controls */}
        <div className="left-column">
          <VoiceControl onLog={addLog} />

          <div className="panel system-status-panel">
            <h2 className="panel__title">&gt; STATUS</h2>
            <div className="status-list">
              <div className="status-item">
                <span className="status-item__label">Voice</span>
                <strong className="status-item__value status-item__value--online">ONLINE</strong>
              </div>
              <div className="status-item">
                <span className="status-item__label">CAM_02</span>
                <strong className="status-item__value status-item__value--online">ACTIVE</strong>
              </div>
              <div className="status-item">
                <span className="status-item__label">CAM_03</span>
                <strong className="status-item__value status-item__value--online">ACTIVE</strong>
              </div>
              <div className="status-item">
                <span className="status-item__label">LeRobot</span>
                <strong className={`status-item__value ${lerobotStatus.running ? 'status-item__value--online' : ''}`}>
                  {lerobotStatus.running ? 'ACTIVE' : 'STANDBY'}
                </strong>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Video Feeds and Terminal */}
        <div className="right-column">
          {/* Two Camera Feeds Side by Side */}
          <div className="video-feeds-container">
            <CVVideoStream 
              streamUrl={`${API_BASE}/api/video/feed`}
              label="FRONT_CAM"
              showDetections={true}
              onPickTarget={handlePickTarget} 
            />
            <CVVideoStream 
              streamUrl={`${API_BASE}/api/video/handeye`}
              label="HANDEYE_CAM"
              showDetections={false}
            />
          </div>

          <SystemLog logs={logs} />
        </div>
      </main>
    </div>
  );
}
