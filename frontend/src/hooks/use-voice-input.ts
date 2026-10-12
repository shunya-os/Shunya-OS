/**
 * useVoiceInput — shared SpeechRecognition hook (extracted from
 * executive-home.tsx so every text surface can have working voice input).
 *
 * Fixes over the original inline implementation:
 *   - duplicate text on stop: final segments are appended ONCE per result
 *     event; interim text is display-only and never committed, so stopping
 *     never re-appends the last utterance; onend only flushes an interim if
 *     the browser never produced a final result for it.
 *   - single-shot mode (continuous=false) for search bars: recognition stops
 *     automatically after a pause and delivers one `onFinal` transcript.
 *   - stop() is always attempted and listening state is reset in a finally
 *     block; the recognition instance is torn down on unmount.
 *   - onerror is handled (not-allowed / audio-capture / network / no-speech)
 *     and surfaced as a visible, translatable error key.
 *
 * API: { supported, listening, transcript, interim, error, start, stop, reset }
 */

import { useCallback, useEffect, useRef, useState } from 'react';

/** Error keys are intentionally stable — render with t(error) for i18n. */
export type VoiceErrorKey =
  | 'voiceUnsupported'
  | 'micPermission'
  | 'noMic'
  | 'networkError'
  | 'noSpeech'
  | 'speechError'
  | 'voiceUnavailable';

export interface VoiceInputState {
  supported: boolean;
  listening: boolean;
  /** Committed final transcript (accumulated when continuous). */
  transcript: string;
  /** Live interim text while listening (display-only, never committed). */
  interim: string;
  /** Stable i18n error key, or null when no error. */
  error: VoiceErrorKey | null;
  start: () => void;
  stop: () => void;
  reset: () => void;
}

interface Options {
  /** true → keep listening until stopped (dictation); false → single shot. */
  continuous?: boolean;
  /** Called with the final transcript when speech completes (single-shot). */
  onFinal?: (text: string) => void;
}

function getRecognitionCtor(): any | null {
  if (typeof window === 'undefined') return null;
  const w = window as any;
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

export function useVoiceInput(lang: string = 'en-US', options: Options = {}): VoiceInputState {
  const { continuous = false, onFinal } = options;
  const [supported] = useState<boolean>(() => getRecognitionCtor() !== null);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interim, setInterim] = useState('');
  const [error, setError] = useState<VoiceErrorKey | null>(null);

  const recognitionRef = useRef<any>(null);
  const committedRef = useRef(''); // committed finals (mirror of `transcript`)
  const interimRef = useRef(''); // live interim (mirror of `interim`)
  const onFinalRef = useRef(onFinal);
  onFinalRef.current = onFinal;

  const handleError = useCallback((code: string | undefined) => {
    if (code === 'aborted') return;
    let key: VoiceErrorKey;
    if (code === 'not-allowed' || code === 'service-not-allowed') key = 'micPermission';
    else if (code === 'audio-capture') key = 'noMic';
    else if (code === 'network') key = 'networkError';
    else if (code === 'no-speech') key = 'noSpeech';
    else key = 'voiceUnavailable';
    setError(key);
    setListening(false);
  }, []);

  const handleResult = useCallback(
    (event: any) => {
      let finals = '';
      let interims = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const segment = result?.[0]?.transcript ?? '';
        if (result.isFinal) finals += segment;
        else interims += segment;
      }
      if (finals) {
        // Continuous: append only new finals. Single-shot: the one final
        // utterance replaces the transcript — never re-appended on stop.
        const next = continuous ? (committedRef.current ? `${committedRef.current} ${finals}` : finals) : finals;
        committedRef.current = next;
        setTranscript(next);
        if (!continuous) {
          const text = finals.trim();
          if (text) onFinalRef.current?.(text);
        }
      }
      interimRef.current = interims;
      setInterim(interims);
    },
    [continuous],
  );

  const stop = useCallback(() => {
    const rec = recognitionRef.current;
    if (rec) {
      try {
        rec.stop();
      } catch {
        /* recognition already stopped — nothing to do */
      } finally {
        // `listening` must reset even if the browser never fires onend.
        setListening(false);
      }
    } else {
      setListening(false);
    }
  }, []);

  const start = useCallback(() => {
    if (listening) return;
    const Ctor = getRecognitionCtor();
    if (!Ctor) {
      setError('voiceUnsupported');
      return;
    }
    // Tear down any stale instance before starting a fresh one.
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.abort();
      } catch {
        /* ignore */
      }
      recognitionRef.current = null;
    }

    setError(null);
    const recognition = new Ctor();
    recognition.continuous = continuous;
    recognition.interimResults = true;
    // Empty lang → browser default (used by the 'auto' language).
    if (lang) recognition.lang = lang;

    recognition.onresult = handleResult;
    recognition.onerror = (event: any) => handleError(event?.error);
    recognition.onend = () => {
      // Single-shot: if the browser ended without finalizing the last interim,
      // flush it once — it can't duplicate because committed finals were
      // already delivered and interimRef is cleared here.
      if (!continuous && interimRef.current) {
        const pending = interimRef.current.trim();
        interimRef.current = '';
        setInterim('');
        if (pending) {
          committedRef.current = pending;
          setTranscript(pending);
          onFinalRef.current?.(pending);
        }
      }
      setInterim('');
      setListening(false);
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
      setListening(true);
    } catch {
      setError('speechError');
      setListening(false);
    }
  }, [continuous, lang, listening, handleResult, handleError]);

  const reset = useCallback(() => {
    committedRef.current = '';
    interimRef.current = '';
    setTranscript('');
    setInterim('');
    setError(null);
  }, []);

  // Unmount cleanup: detach handlers first so no late events touch React
  // state, then abort. stop() is always attempted (finally semantics).
  useEffect(() => {
    return () => {
      const rec = recognitionRef.current;
      if (rec) {
        try {
          rec.onresult = null;
          rec.onerror = null;
          rec.onend = null;
        } catch {
          /* ignore */
        }
        try {
          rec.stop();
        } catch {
          /* ignore */
        } finally {
          try {
            rec.abort();
          } catch {
            /* ignore */
          }
        }
      }
    };
  }, []);

  return { supported, listening, transcript, interim, error, start, stop, reset };
}