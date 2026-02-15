import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Scrapple — Voice Control Component
 * ===================================
 * Combined voice interaction flow:
 * 1. User clicks "RUN ONCE" → Gemini speaks what it sees
 * 2. User speaks → Text shows in transcript
 * 3. Gemini evaluates → If positive, auto-execute LeRobot
 */

const API_BASE = 'http://localhost:5000';

// Web Speech API types
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface VoiceControlProps {
  onLog?: (type: 'user' | 'bot' | 'system', text: string) => void;
}

type FlowState = 'idle' | 'announcing' | 'listening' | 'processing' | 'executing' | 'error';

export default function VoiceControl({ onLog }: VoiceControlProps) {
  const [flowState, setFlowState] = useState<FlowState>('idle');
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [geminiResult, setGeminiResult] = useState<{ valid: boolean; target: string | null; reason: string } | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const finalTranscriptRef = useRef('');

  // Check for Web Speech API support
  useEffect(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      setIsSupported(false);
      setErrorMsg('Web Speech API not supported. Use Chrome or Edge.');
    }
  }, []);

  // Start the voice flow
  const startVoiceFlow = useCallback(async () => {
    if (flowState !== 'idle') return;
    
    setFlowState('announcing');
    setTranscript('');
    setInterimTranscript('');
    setGeminiResult(null);
    setErrorMsg(null);
    finalTranscriptRef.current = '';

    try {
      // Step 1: Call backend to announce visible objects via TTS
      onLog?.('system', '▶ Starting voice command cycle...');
      
      const announceRes = await fetch(`${API_BASE}/api/voice/announce`, {
        method: 'POST',
      });
      
      if (!announceRes.ok) {
        throw new Error('Failed to announce');
      }
      
      const announceData = await announceRes.json();
      onLog?.('bot', announceData.spoken || 'Scanning...');
      
      // Step 2: Wait for TTS to finish, then start listening
      // Give TTS about 3 seconds
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Step 3: Start speech recognition
      startListening();
      
    } catch (err) {
      console.error('[VoiceControl] Announce error:', err);
      setErrorMsg('Failed to start voice flow');
      setFlowState('error');
      onLog?.('system', `Error: ${err}`);
      setTimeout(() => setFlowState('idle'), 2000);
    }
  }, [flowState, onLog]);

  // Start speech recognition
  const startListening = useCallback(() => {
    if (!isSupported) return;
    
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) return;

    setFlowState('listening');
    onLog?.('system', '🎤 Listening for command...');

    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = false; // Stop after first result
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      finalTranscriptRef.current = '';
      setTranscript('');
      setInterimTranscript('');
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          final += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }

      if (final) {
        finalTranscriptRef.current += final;
        setTranscript(finalTranscriptRef.current);
      }
      
      setInterimTranscript(interim);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('[VoiceControl] Speech error:', event.error);
      if (event.error === 'no-speech') {
        setErrorMsg('No speech detected. Try again.');
        onLog?.('system', '❌ No speech detected');
      } else if (event.error === 'not-allowed') {
        setErrorMsg('Microphone access denied.');
        onLog?.('system', '❌ Microphone access denied');
      } else {
        setErrorMsg(`Speech error: ${event.error}`);
      }
      setFlowState('error');
      setTimeout(() => setFlowState('idle'), 2000);
    };

    recognition.onend = () => {
      // Send final transcript to Gemini for evaluation
      if (finalTranscriptRef.current.trim()) {
        onLog?.('user', `"${finalTranscriptRef.current}"`);
        evaluateCommand(finalTranscriptRef.current);
      } else {
        setFlowState('idle');
        onLog?.('system', '■ No command detected');
      }
    };

    recognitionRef.current = recognition;
    
    try {
      recognition.start();
    } catch (err) {
      console.error('[VoiceControl] Failed to start:', err);
      setErrorMsg('Failed to start speech recognition');
      setFlowState('error');
    }
  }, [isSupported, onLog]);

  // Evaluate command with Gemini and auto-execute LeRobot if positive
  const evaluateCommand = useCallback(async (command: string) => {
    setFlowState('processing');
    onLog?.('system', '🧠 Processing with Gemini...');

    try {
      const res = await fetch(`${API_BASE}/api/voice/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });
      
      const data = await res.json();
      
      if (data.decision) {
        setGeminiResult(data.decision);
        
        if (data.decision.valid) {
          onLog?.('system', `✅ ACCEPTED: ${data.decision.reason}`);
          onLog?.('bot', data.tts_result || `Targeting: ${data.decision.target}`);
          
          // Auto-execute LeRobot - the backend already calls run_lerobot_commands
          // But let's also trigger /api/lerobot/run for the command output
          setFlowState('executing');
          onLog?.('system', `🤖 Executing LeRobot for: ${data.decision.target}`);
          
          try {
            await fetch(`${API_BASE}/api/lerobot/run`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
            });
            onLog?.('system', '🤖 LeRobot command triggered');
          } catch (err) {
            console.error('[VoiceControl] LeRobot error:', err);
          }
          
          setFlowState('idle');
          onLog?.('system', '■ Cycle complete');
        } else {
          onLog?.('system', `❌ REJECTED: ${data.decision.reason}`);
          onLog?.('bot', data.tts_result || data.decision.reason);
          setFlowState('idle');
        }
      } else {
        setFlowState('idle');
      }
      
    } catch (err) {
      console.error('[VoiceControl] Evaluate error:', err);
      setErrorMsg('Failed to evaluate command');
      setFlowState('error');
      onLog?.('system', `Error: ${err}`);
      setTimeout(() => setFlowState('idle'), 2000);
    }
  }, [onLog]);

  // Stop any ongoing recognition
  const stopFlow = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.abort();
    }
    setFlowState('idle');
  }, []);

  // Terminate LeRobot process and reset UI
  const terminateLeRobot = useCallback(async () => {
    try {
      // Stop any ongoing recognition
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      
      // Call the kill endpoint
      const res = await fetch(`${API_BASE}/api/lerobot/kill`, { method: 'POST' });
      const data = await res.json();
      onLog?.('system', data.message || 'LeRobot terminated');
      
      // Reset ALL state
      setFlowState('idle');
      setTranscript('');
      setInterimTranscript('');
      setGeminiResult(null);
      setErrorMsg('');
      
      onLog?.('system', '■ UI reset');
    } catch (err) {
      onLog?.('system', `Failed to terminate: ${err}`);
      // Still reset UI even on error
      setFlowState('idle');
      setTranscript('');
      setGeminiResult(null);
    }
  }, [onLog]);

  // Get button text based on state
  const getButtonText = () => {
    switch (flowState) {
      case 'announcing': return '📢 ANNOUNCING...';
      case 'listening': return '🎤 LISTENING...';
      case 'processing': return '🧠 PROCESSING...';
      case 'executing': return '🤖 EXECUTING...';
      case 'error': return '⚠️ ERROR';
      default: return '▶ RUN ONCE';
    }
  };

  const isRunning = flowState !== 'idle' && flowState !== 'error';

  return (
    <div className="panel">
      {/* Header */}
      <h2 className="panel__title">Voice Control</h2>

      {/* Main Button */}
      <button
        onClick={isRunning ? stopFlow : startVoiceFlow}
        disabled={!isSupported || flowState === 'executing'}
        className={`demo-button w-full ${isRunning ? 'demo-button--running' : 'demo-button--idle'}`}
      >
        {getButtonText()}
      </button>

      {/* Status Indicator */}
      <div className="flex items-center gap-2 mt-3 text-xs">
        <span 
          className="w-2 h-2 rounded-full"
          style={{ 
            background: flowState === 'idle' ? '#00ff41' : 
                       flowState === 'error' ? '#ff0033' : '#ffaa00',
            boxShadow: `0 0 6px ${flowState === 'idle' ? '#00ff41' : 
                                 flowState === 'error' ? '#ff0033' : '#ffaa00'}`
          }}
        />
        <span className="text-[var(--text-muted)] uppercase tracking-wider">
          {flowState === 'idle' ? 'READY' : flowState.toUpperCase()}
        </span>
      </div>

      {/* Transcript Display */}
      <div className="bg-black/50 border border-[var(--green-dim)] p-3 mt-3 min-h-[80px]">
        <div className="text-[9px] text-[var(--text-dim)] uppercase tracking-widest mb-2">&gt; TRANSCRIPT_</div>
        <div className="font-mono text-xs">
          {transcript && (
            <span className="text-[var(--green)]">{transcript}</span>
          )}
          {interimTranscript && (
            <span className="text-[var(--amber)] opacity-70">{interimTranscript}</span>
          )}
          {!transcript && !interimTranscript && (
            <span className="text-[var(--text-dead)]">
              {flowState === 'listening' ? 'LISTENING...' : 'AWAITING_INPUT...'}
            </span>
          )}
          <span className="cursor-blink"></span>
        </div>
      </div>

      {/* Gemini Result */}
      {geminiResult && (
        <div className={`mt-3 p-3 border ${geminiResult.valid ? 'border-[var(--green)] bg-[var(--green-dim)]' : 'border-[var(--red)] bg-[var(--red-dim)]'}`}>
          <div className="text-[9px] uppercase tracking-widest mb-1">
            <span className={geminiResult.valid ? 'text-[var(--green)]' : 'text-[var(--red)]'}>
              {geminiResult.valid ? '> TARGET_ACQUIRED' : '> INVALID_COMMAND'}
            </span>
          </div>
          {geminiResult.target && (
            <div className="text-sm font-mono font-bold text-[var(--green)] mb-1">
              {geminiResult.target.toUpperCase()}
            </div>
          )}
          <div className="text-[10px] text-[var(--text-dim)]">{geminiResult.reason}</div>
        </div>
      )}

      {/* Error Display */}
      {errorMsg && (
        <div className="mt-3 border border-[var(--red)] bg-[var(--red-dim)] p-2 text-[var(--red)] text-[10px]">
          ERROR: {errorMsg}
        </div>
      )}

      {/* Terminate Button */}
      <button
        onClick={terminateLeRobot}
        className="hacker-btn hacker-btn--danger w-full mt-4"
      >
        [TERMINATE_PROCESS]
      </button>

      {/* Help Text */}
      <div className="text-[9px] text-[var(--text-dead)] text-center tracking-wider mt-3">
        Say: "pick the [object]" or "grab the [object]"
      </div>
    </div>
  );
}
