/**
 * Scrapple — Voice Control Component
 * ====================================
 * One-shot microphone trigger for voice commands.
 *
 * When clicked, calls POST /api/voice/listen and returns result via callback.
 * Disabled when demo loop is running.
 */

import { useState } from 'react';

interface VoiceControlProps {
  onListeningStart: () => void;
  onListeningEnd: (data: Record<string, unknown>) => void;
  disabled?: boolean;
}

const API_BASE = 'http://localhost:5000';

export default function VoiceControl({
  onListeningStart,
  onListeningEnd,
  disabled = false,
}: VoiceControlProps) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePushToTalk = async () => {
    if (disabled || isListening || isProcessing) return;

    setIsListening(true);
    onListeningStart();

    try {
      const response = await fetch(`${API_BASE}/api/voice/listen`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: 4 }),
      });

      setIsListening(false);
      setIsProcessing(true);

      const data = await response.json();
      onListeningEnd(data);
    } catch (error) {
      console.error('Voice Error:', error);
      onListeningEnd({ error: 'Connection Failed' });
    } finally {
      setIsListening(false);
      setIsProcessing(false);
    }
  };

  return (
    <div className="bg-gray-800 border border-green-800 rounded-lg p-4">
      <h2 className="text-sm font-bold uppercase tracking-wider mb-4 text-green-300">
        Voice Command
      </h2>

      {/* Mic Button */}
      <div className="flex flex-col items-center">
        <button
          type="button"
          onClick={handlePushToTalk}
          disabled={disabled || isListening || isProcessing}
          className={`
            w-24 h-24 rounded-full border-4 flex items-center justify-center
            transition-all duration-200
            ${
              isListening
                ? 'border-red-500 bg-red-900/30 animate-pulse'
                : isProcessing
                ? 'border-yellow-500 bg-yellow-900/30'
                : 'border-green-500 bg-green-900/30 hover:bg-green-800/50'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          {isListening ? (
            <span className="text-3xl">🎙️</span>
          ) : isProcessing ? (
            <span className="text-3xl animate-spin">⚙️</span>
          ) : (
            <span className="text-3xl">🎤</span>
          )}
        </button>

        {/* Status Text */}
        <div className="mt-3 text-xs text-center">
          {disabled && !isListening && !isProcessing && (
            <span className="text-gray-500">Demo loop active</span>
          )}
          {!disabled && isListening && (
            <span className="text-red-400">LISTENING...</span>
          )}
          {!disabled && isProcessing && (
            <span className="text-yellow-400">PROCESSING...</span>
          )}
          {!disabled && !isListening && !isProcessing && (
            <span className="text-green-600">Click to speak</span>
          )}
        </div>
      </div>
    </div>
  );
}