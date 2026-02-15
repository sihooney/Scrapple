/**
 * Scrapple — System Log Component
 * ================================
 * Apocalyptic terminal log display.
 */

import { useEffect, useRef } from 'react';

interface LogEntry {
  id: number;
  type: 'user' | 'bot' | 'system';
  text: string;
  timestamp: string;
}

interface SystemLogProps {
  logs: LogEntry[];
}

export default function SystemLog({ logs }: SystemLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [logs]);

  const reversedLogs = [...logs].reverse();

  const getPrefix = (type: string) => {
    switch (type) {
      case 'user': return '[USR]';
      case 'bot': return '[BOT]';
      default: return '[SYS]';
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case 'user': return 'text-[#00ff41]';
      case 'bot': return 'text-[#00ffff]';
      default: return 'text-[#ffaa00]';
    }
  };

  return (
    <div className="system-log flex-1 min-h-0">
      {/* Header */}
      <div className="bg-[var(--bg-dark)] border-b border-[var(--green-dim)] px-3 py-2 flex items-center justify-between">
        <span className="text-[var(--green)] font-mono text-[11px] font-bold tracking-widest uppercase">
          &gt; SYSTEM_LOG
        </span>
        <span className="text-[9px] text-[var(--text-dead)] tracking-wider">
          [{reversedLogs.length} ENTRIES]
        </span>
      </div>

      {/* Log Content */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-3 font-mono text-[10px] space-y-1"
        style={{ maxHeight: 'calc(100% - 40px)' }}
      >
        {logs.length === 0 && (
          <div className="text-[var(--text-dead)]">
            &gt; AWAITING_INPUT...<span className="cursor-blink"></span>
          </div>
        )}

        {reversedLogs.map((log) => (
          <div key={log.id} className="flex gap-2 leading-relaxed">
            <span className="text-[var(--text-dead)] flex-shrink-0 opacity-50">
              {log.timestamp}
            </span>
            <span className={`flex-shrink-0 ${getColor(log.type)}`}>
              {getPrefix(log.type)}
            </span>
            <span className={getColor(log.type)}>
              {log.text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}