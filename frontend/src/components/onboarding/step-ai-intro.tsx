/**
 * Step: AI Introduction (Z-03A Article XI).
 *
 * Checks AI availability via API call. If AI is healthy, shows the existing
 * intro with a test prompt. If AI is unavailable, shows explanation + Skip button.
 * Always allows skipping.
 */

import { useState, useRef, useEffect } from 'react';
import { api } from '../../api/client';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  onNext: () => void;
  onBack: () => void;
}

type DemoPhase = 'idle' | 'loading' | 'success' | 'error';
type AIHealth = 'checking' | 'healthy' | 'unavailable' | 'error';

const SAMPLE_QUESTION = 'Ask me anything about your business—like "What are my top priorities?"';

export function StepAiIntro({ onNext, onBack }: Props) {
  const [aiHealth, setAiHealth] = useState<AIHealth>('checking');
  const [healthMsg, setHealthMsg] = useState('');
  const [demoPhase, setDemoPhase] = useState<DemoPhase>('idle');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Check AI health on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await api.checkAIHealth();
        if (cancelled) return;
        if (resp.success) {
          setAiHealth('healthy');
        } else {
          setAiHealth('unavailable');
          setHealthMsg(resp.error ?? 'AI service is not responding.');
        }
      } catch {
        if (!cancelled) {
          setAiHealth('unavailable');
          setHealthMsg('AI service is not available right now. You can enable it later from settings.');
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (aiHealth === 'healthy') {
      inputRef.current?.focus();
    }
  }, [aiHealth]);

  const handleAsk = async () => {
    if (!question.trim()) return;
    setDemoPhase('loading');
    setErrorMsg('');
    setAnswer('');

    try {
      const resp = await api.askIntelligence(question.trim());
      if (resp.success && resp.answer) {
        setAnswer(resp.answer);
        setDemoPhase('success');
      } else {
        setDemoPhase('error');
        setErrorMsg(resp.error ?? 'No response from AI. Please try again.');
      }
    } catch {
      setDemoPhase('error');
      setErrorMsg('Could not reach the AI service. The server may not be running.');
    }
  };

  const handleContinue = () => {
    onNext();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && demoPhase !== 'loading' && aiHealth === 'healthy') {
      e.preventDefault();
      if (question.trim()) {
        handleAsk();
      } else {
        handleContinue();
      }
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      onBack();
    }
  };

  const handleRetry = () => {
    setDemoPhase('idle');
    setErrorMsg('');
    setAnswer('');
  };

  return (
    <div className="sh-onboarding" onKeyDown={handleKeyDown}>
      <div className="sh-onboarding-content">
        <div className="sh-onboarding-card sh-onb-fade-in">
          <div className="sh-onboarding-title">Meet Your AI</div>

          {/* ── AI Health Check ── */}
          {aiHealth === 'checking' && (
            <div className="sh-onboarding-info" style={{ width: '100%', textAlign: 'center' }}>
              <span className="sh-onboarding-spinner" />
              <span style={{ marginLeft: 8 }}>Checking AI availability…</span>
            </div>
          )}

          {/* ── AI Unavailable ── */}
          {aiHealth === 'unavailable' && (
            <>
              <div className="sh-onboarding-subtitle">SHUNYA's intelligence engine helps you manage your business.</div>
              <div className="sh-onboarding-error" role="alert" style={{ width: '100%' }}>
                <div style={{ fontWeight: 500, marginBottom: 4 }}>AI is not available right now</div>
                <div>{healthMsg}</div>
                <div style={{ fontSize: '0.75rem', marginTop: 6, opacity: 0.8 }}>
                  You can enable AI later from your workspace settings.
                </div>
              </div>
              <button className="sh-onboarding-btn" onClick={handleContinue} autoFocus tabIndex={0}>
                Skip ›
              </button>
            </>
          )}

          {/* ── AI Healthy — Show Intro ── */}
          {aiHealth === 'healthy' && (
            <>
              <div className="sh-onboarding-subtitle">
                SHUNYA's intelligence engine helps you manage your business—answering questions, generating insights,
                and automating tasks. It learns from your organization's data to provide relevant, contextual responses.
              </div>

              {/* Sample message */}
              <div className="sh-onboarding-ai-message">
                <div className="sh-onboarding-ai-label">SHUNYA AI</div>
                {SAMPLE_QUESTION}
              </div>

              {/* Demo input */}
              <div className="sh-onboarding-field" style={{ width: '100%' }}>
                <label htmlFor="ai-demo-input">Try it yourself</label>
                <textarea
                  id="ai-demo-input"
                  className="sh-onboarding-textarea"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Type a question about your business..."
                  disabled={demoPhase === 'loading'}
                  ref={inputRef}
                  tabIndex={0}
                  rows={3}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if (question.trim()) handleAsk();
                    }
                  }}
                />
              </div>

              {/* AI response */}
              {demoPhase === 'success' && answer && (
                <div className="sh-onboarding-ai-message">
                  <div className="sh-onboarding-ai-label">SHUNYA AI Response</div>
                  {answer}
                </div>
              )}

              {demoPhase === 'error' && (
                <div className="sh-onboarding-error" role="alert">
                  {errorMsg}
                  <div style={{ marginTop: 8 }}>
                    <button
                      className="sh-onboarding-btn-secondary"
                      onClick={handleRetry}
                      style={{ padding: '6px 12px', fontSize: '0.8rem', width: 'auto' }}
                      tabIndex={0}
                    >
                      Retry
                    </button>
                  </div>
                </div>
              )}

              <div className="sh-onboarding-btn-row">
                {question.trim() && demoPhase !== 'loading' ? (
                  <button className="sh-onboarding-btn" onClick={handleAsk} tabIndex={0}>
                    Ask
                  </button>
                ) : null}
                {demoPhase === 'loading' && (
                  <button className="sh-onboarding-btn" disabled>
                    <span className="sh-onboarding-spinner" />
                    Thinking…
                  </button>
                )}
                <button
                  className="sh-onboarding-btn"
                  onClick={handleContinue}
                  tabIndex={0}
                  style={demoPhase === 'success' || !question.trim() ? {} : { display: 'none' }}
                >
                  {demoPhase === 'success' || !question.trim() ? 'Continue' : 'Skip ›'}
                </button>
              </div>
            </>
          )}

          {aiHealth !== 'checking' && (
            <button
              className="sh-onboarding-btn-secondary"
              onClick={onBack}
              disabled={demoPhase === 'loading'}
              tabIndex={0}
            >
              Back
            </button>
          )}
        </div>
      </div>
      <style>{onboardingStyles}</style>
    </div>
  );
}
