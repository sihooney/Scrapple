/**
 * Scrapple — System Log Component
 * ================================
 * Live terminal-style log display.
 * New logs appear at the TOP (reversed order).
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

  // Auto-scroll to top on new logs
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [logs]);

  // Reverse logs so newest appears first
  const reversedLogs = [...logs].reverse();

  return (
    <div className="bg-gray-950 border-2 border-cyan-500/40 rounded-lg overflow-hidden flex flex-col h-full glow-cyan">
      <div className="bg-gray-900 border-b border-cyan-500/40 px-4 py-3 flex items-center justify-between">
        <span className="text-cyan-400 font-mono font-bold uppercase tracking-wider text-sm">
          Terminal
        </span>
        <div className="flex gap-2" aria-hidden="true">
          <div className="w-3 h-3 rounded-full bg-red-500 shadow-lg shadow-red-500/50" />
          <div className="w-3 h-3 rounded-full bg-yellow-500 shadow-lg shadow-yellow-500/50" />
          <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50" />
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto scrollbar-hide space-y-1 p-4 font-mono text-xs"
      >
        {logs.length === 0 && (
          <div className="text-cyan-600/50">
            -- Awaiting commands --
          </div>
        )}

        {reversedLogs.map((log) => (
          <div key={log.id} className="flex gap-3 min-h-fit">
            <span className="text-cyan-600 flex-shrink-0">
              {log.timestamp}
            </span>
            <div
              className={`flex-1 ${
                log.type === 'user'
                  ? 'text-emerald-400'
                  : log.type === 'bot'
                  ? 'text-cyan-400'
                  : 'text-yellow-300'
              }`}
            >
              {log.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}