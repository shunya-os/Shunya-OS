/**
 * SHUNYA Primary Workspace — FOCUS + WORLD architecture.
 *
 * Constitutional recovery: SHUNYA must provide BOTH:
 *   (A) A complete, familiar organizational workspace the human can explore
 *   (B) An intelligent operating layer that understands and guides
 *
 * Principle: INTELLIGENCE COMPRESSES COMPLEXITY WITHOUT DESTROYING ACCESS TO REALITY.
 *
 * ── Layout ────────────────────────────────────────────────────
 * Zone Left (280px): Organizational Orientation — domains, context
 * Zone Center (flex:1): Primary Focus — attention, object work, greeting
 * Zone Bottom: Integrated Command + Voice
 *
 * ── Architecture ──────────────────────────────────────────────
 * FOCUS: What the human is working on OR what SHUNYA recommends
 * WORLD: Remaining organization is always accessible, never hidden
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLivingStore } from '../living-workspace/living-store';
import { useWorkspaceStore } from '../../runtimes/workspace/store';
import { useActiveWorkspace } from '../../hooks/workspace-hooks';
import { ObjectWorkspaceViewer } from '../workspace/object-workspace-viewer';
import { AdminPanel } from '../workspace/admin-panel';
import { ImportExportPanel } from '../workspace/import-export-panel';
import { CommitmentWorkspace } from '../commitment/commitment-workspace';
import { ConversationWorkspace } from '../conversation/conversation-workspace';
import { CommercialWorkspace } from '../commercial/commercial-workspace';
import { RelationshipWorkspace } from '../relationship/relationship-workspace';
import { MarketingWorkspace } from '../marketing/marketing-workspace';
import { SalesPipeline } from '../sales/sales-pipeline';
import { ExecutionWorkspace } from '../work/execution-workspace';
import { OutputsBrowser } from '../outputs/outputs-browser';
import { OrganizationBrowser } from '../organization/organization-browser';
import { LeadManagement } from '../sales/lead-management';
import { subscribeSSE } from '../../runtimes/sse-runtime';

// ═══════════════════════════════════════════════════════════════════
// DOMAIN DEFINITIONS — Universal organizational domains
// ═══════════════════════════════════════════════════════════════════

interface Domain {
  id: string;
  label: string;
  icon: string;
  description: string;
  wsType: string;
  count?: number;
}

const ORGANIZATIONAL_DOMAINS: Domain[] = [
  { id: 'people', label: 'People', icon: '👤', description: 'Identities, team members, contacts', wsType: 'people' },
  { id: 'conversations', label: 'Conversations', icon: '💬', description: 'All conversations and discussions', wsType: 'conversation' },
  { id: 'work', label: 'Work', icon: '◉', description: 'Tasks, executions, SHUNYA work', wsType: 'commitment' },
  { id: 'finance', label: 'Finance', icon: '◇', description: 'Financial information, transactions', wsType: 'object' },
  { id: 'commercial', label: 'Commercial', icon: '◆', description: 'Deals, opportunities, revenue', wsType: 'object' },
  { id: 'marketing', label: 'Marketing', icon: '○', description: 'Campaigns, content, outreach', wsType: 'object' },
  { id: 'sales', label: 'Sales', icon: '⬡', description: 'Proposals, customers, pipeline', wsType: 'object' },
  { id: 'operations', label: 'Operations', icon: '△', description: 'Processes, resources, inventory', wsType: 'object' },
  { id: 'knowledge', label: 'Knowledge', icon: '◎', description: 'Docs, research, references', wsType: 'object' },
  { id: 'outputs', label: 'Outputs', icon: '✓', description: 'Generated results, reports, artifacts', wsType: 'object' },
  { id: 'memory', label: 'Memory', icon: '◈', description: 'SHUNYA memory, reflections, history', wsType: 'object' },
  { id: 'relationships', label: 'Relationships', icon: '◈', description: 'Connections between people and entities', wsType: 'object' },
];

// ═══════════════════════════════════════════════════════════════════
// 1. SHUNYA PRESENCE
// ═══════════════════════════════════════════════════════════════════

function PresenceIndicator({ mode }: { mode: 'calm' | 'working' | 'attentive' | 'active' }) {
  const dotColor = mode === 'calm' ? 'var(--shunya-success, #6a9f6a)'
    : mode === 'working' ? 'var(--shunya-info, #4a9e9e)'
    : mode === 'attentive' ? 'var(--shunya-gold, #a4865f)'
    : 'var(--shunya-gold, #a4865f)';

  const label = mode === 'calm' ? 'Observing'
    : mode === 'working' ? 'Working'
    : mode === 'attentive' ? 'I notice something'
    : 'Present';

  return (
    <div className="pw-presence">
      <motion.span
        className="pw-presence-dot"
        style={{ backgroundColor: dotColor, boxShadow: `0 0 6px ${dotColor}` }}
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
      />
      <span className="pw-presence-label">{label}</span>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 2. ORGANIZATIONAL ORIENTATION — Zone Left
// ═══════════════════════════════════════════════════════════════════

function OrganizationalOrientation({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const handleDomainClick = useCallback((domain: Domain) => {
    useWorkspaceStore.getState().open(domain.label, domain.wsType as any, {
      objectType: domain.id,
      objectId: domain.id,
    });
  }, []);

  return (
    <motion.aside
      className="pw-org-orientation"
      animate={{ width: collapsed ? 0 : 260, opacity: collapsed ? 0 : 1 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      aria-label="Organizational orientation"
    >
      <div className="pw-org-header">
        <span className="pw-org-title">Organization</span>
        <button className="pw-org-toggle" onClick={onToggle} aria-label={collapsed ? 'Expand' : 'Collapse'}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <polyline points={collapsed ? '9 4 5 7 9 10' : '5 4 9 7 5 10'} />
          </svg>
        </button>
      </div>
      <div className="pw-org-domains">
        <p className="pw-org-hint">What's in your organization</p>
        {ORGANIZATIONAL_DOMAINS.map((domain) => (
          <button
            key={domain.id}
            className="pw-org-domain"
            onClick={() => handleDomainClick(domain)}
            title={domain.description}
          >
            <span className="pw-org-domain-icon">{domain.icon}</span>
            <span className="pw-org-domain-label">{domain.label}</span>
            {domain.count !== undefined && (
              <span className="pw-org-domain-count">{domain.count}</span>
            )}
          </button>
        ))}
      </div>
      <p className="pw-org-footer">Ask SHUNYA or click to explore any area</p>
    </motion.aside>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 3. WHAT MATTERS NOW — Primary attention item
// ═══════════════════════════════════════════════════════════════════

function WhatMattersNow() {
  const signals = useLivingStore((s) => s.awarenessSignals);
  const count = useLivingStore((s) => s.awarenessCount);
  const calm = useLivingStore((s) => s.awarenessCalm);
  const acknowledgeSignal = useLivingStore((s) => s.acknowledgeSignal);
  const dismissSignal = useLivingStore((s) => s.dismissSignal);

  if (calm) return null;
  if (!signals || signals.length === 0) return null;

  const top = signals[0];
  const priorityIcon = top.priority === 'critical' ? '⬡'
    : top.priority === 'high' ? '◈' : '◇';

  const handleOpen = () => {
    if (top.affected_object_id && top.affected_object_type) {
      useWorkspaceStore.getState().open(top.title, 'object', {
        objectType: top.affected_object_type,
        objectId: top.affected_object_id,
      });
    }
  };

  return (
    <motion.div
      className="pw-attention"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 200, damping: 20 }}
    >
      <div className={`pw-attention-header pw-attention-${top.priority}`}>
        <span className="pw-attention-priority">{priorityIcon} SHUNYA recommends focusing here</span>
        {count > 1 && <span className="pw-attention-count">+{count - 1} more</span>}
      </div>
      <h2 className="pw-attention-title">{top.title}</h2>
      {top.description && <p className="pw-attention-reason">{top.description}</p>}
      {top.reason && <p className="pw-attention-why">Why: {top.reason}</p>}
      {top.suggested_action && (
        <p className="pw-attention-action">→ {top.suggested_action}</p>
      )}
      <div className="pw-attention-actions">
        <button className="pw-attention-btn pw-attention-btn-primary" onClick={() => acknowledgeSignal(top.signal_id)}>
          Acknowledge
        </button>
        {top.affected_object_id && (
          <button className="pw-attention-btn" onClick={handleOpen}>
            Open
          </button>
        )}
        <button className="pw-attention-btn pw-attention-btn-ghost" onClick={() => dismissSignal(top.signal_id)}>
          Not now — I'll focus on something else
        </button>
      </div>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 4. COMPANION GREETING
// ═══════════════════════════════════════════════════════════════════

function CompanionGreeting() {
  const observations = useLivingStore((s) => s.observations);
  const executionHistory = useLivingStore((s) => s.executionHistory);
  const realityEvents = useLivingStore((s) => s.realityEvents);

  const completedCount = executionHistory.filter(e => e.status === 'completed').length;
  const observationCount = observations.length;
  const hasAnyActivity = completedCount > 0 || observationCount > 0 || realityEvents.length > 0;

  if (!hasAnyActivity) return null;

  let message = '';
  if (completedCount > 0) {
    message = `I completed ${completedCount} task${completedCount > 1 ? 's' : ''} since your last visit.`;
    if (observationCount > 0) {
      message += ` I also noticed ${observationCount} thing${observationCount > 1 ? 's' : ''} worth reviewing.`;
    }
  } else if (observationCount > 0) {
    message = `I noticed ${observationCount} change${observationCount > 1 ? 's' : ''} since you were last here.`;
  } else {
    message = `I've been watching — ${realityEvents.length} event${realityEvents.length > 1 ? 's' : ''} recorded.`;
  }

  return (
    <motion.div
      className="pw-greeting"
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <p className="pw-greeting-text">{message}</p>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 5. NARRATIVE STREAM — What's happening
// ═══════════════════════════════════════════════════════════════════

function NarrativeStream() {
  const realityEvents = useLivingStore((s) => s.realityEvents);
  const realityLoading = useLivingStore((s) => s.realityLoading);
  const observations = useLivingStore((s) => s.observations);

  if (realityLoading && realityEvents.length === 0) {
    return <div className="pw-narrative"><p className="pw-narrative-empty">SHUNYA is gathering information…</p></div>;
  }

  if (realityEvents.length === 0 && observations.length === 0) return null;

  return (
    <div className="pw-narrative">
      <div className="pw-narrative-header">
        <span className="pw-narrative-label">What's happening</span>
      </div>
      <div className="pw-narrative-items">
        {realityEvents.slice(0, 5).map((event) => (
          <div key={event.id} className="pw-narrative-item">
            <span className={`pw-narrative-dot ${event.importance === 'high' || event.importance === 'critical' ? 'pw-narrative-dot-important' : ''}`} />
            <div className="pw-narrative-body">
              <span className="pw-narrative-text">{event.title}</span>
              {event.description && event.description !== event.title && (
                <span className="pw-narrative-detail">{event.description}</span>
              )}
              <span className="pw-narrative-time">{_timeAgo(event.timestamp)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function _timeAgo(ts: string): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    const diff = Date.now() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch { return ''; }
}

// ═══════════════════════════════════════════════════════════════════
// 6. CALM STATE
// ═══════════════════════════════════════════════════════════════════

function CalmState() {
  const realityEvents = useLivingStore((s) => s.realityEvents);
  const observations = useLivingStore((s) => s.observations);
  const lastUpdated = useLivingStore((s) => s.lastUpdated);
  const hasActivity = realityEvents.length > 0 || observations.length > 0;

  return (
    <div className="pw-calm">
      <div className="pw-calm-brand">शून्य</div>
      {hasActivity ? (
        <p className="pw-calm-text">Nothing I can currently see requires your attention. Everything is being monitored.</p>
      ) : (
        <p className="pw-calm-text">I have limited recent information. I'm watching — I'll let you know when I notice something meaningful.</p>
      )}
      <p className="pw-calm-action">Explore your organization on the left, or ask SHUNYA anything.</p>
      {lastUpdated && <span className="pw-calm-updated">Updated {_timeAgo(lastUpdated)}</span>}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 7. WORK VISIBILITY — SHUNYA work, tasks, outputs
// ═══════════════════════════════════════════════════════════════════

function WorkVisibility() {
  const activeExecutions = useLivingStore((s) => s.activeExecutions);
  const executionHistory = useLivingStore((s) => s.executionHistory);
  const [expanded, setExpanded] = useState(false);

  const hasWork = activeExecutions.length > 0 || executionHistory.length > 0;
  if (!hasWork) return null;

  return (
    <div className="pw-work">
      <div className="pw-work-header" onClick={() => setExpanded(!expanded)}>
        <span className="pw-work-label">
          {activeExecutions.length > 0
            ? `SHUNYA is working on ${activeExecutions.length} task${activeExecutions.length > 1 ? 's' : ''}`
            : `${executionHistory.length} completed task${executionHistory.length > 1 ? 's' : ''}`}
        </span>
        <span className="pw-work-toggle">{expanded ? '▲' : '▼'}</span>
      </div>
      <AnimatePresence>
        {expanded && (
          <motion.div
            className="pw-work-items"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            {activeExecutions.map((exec) => (
              <div key={exec.id} className="pw-work-item pw-work-active">
                <span className="pw-work-status">⟳</span>
                <span className="pw-work-text">{exec.label}</span>
                <span className="pw-work-owner">SHUNYA</span>
                <span className="pw-work-track">
                  <span className="pw-work-fill" style={{ width: `${Math.round(exec.progress * 100)}%` }} />
                </span>
              </div>
            ))}
            {executionHistory.slice(-3).reverse().map((exec) => (
              <div key={exec.id} className="pw-work-item pw-work-done">
                <span className="pw-work-status">✓</span>
                <span className="pw-work-text">{exec.label}</span>
                <span className="pw-work-owner">
                  {exec.status === 'completed' ? 'SHUNYA' : 'Failed'}
                </span>
                {exec.completed_at && <span className="pw-work-time">{_timeAgo(exec.completed_at)}</span>}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 8. VOICE INPUT — Draft/correction experience
// ═══════════════════════════════════════════════════════════════════

// Check if SpeechRecognition is available
const HAS_SPEECH = typeof window !== 'undefined' && (
  'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
);

const HAS_TTS = typeof window !== 'undefined' && 'speechSynthesis' in window;

// ── TTS Output ──────────────────────────────────────────────
function speakText(text: string) {
  if (!HAS_TTS) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  // Pick a voice
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.lang.startsWith('en') && v.name.includes('Google')) || voices[0];
  if (preferred) utterance.voice = preferred;
  window.speechSynthesis.speak(utterance);
}

function VoiceInput({ onTranscript }: { onTranscript: (text: string) => void }) {
  const [listening, setListening] = useState(false);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  const toggleListening = useCallback(() => {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    if (!HAS_SPEECH) {
      setError('Voice input is not supported in this browser.');
      return;
    }
    setError(null);
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let final = '';
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) final += transcript;
        else interim += transcript;
      }
      setDraft((prev) => prev + final + (interim ? ` (${interim}…)` : ''));
    };

    recognition.onerror = (event: any) => {
      setError(`Voice error: ${event.error}`);
      setListening(false);
    };

    recognition.onend = () => setListening(false);
    recognition.start();
    recognitionRef.current = recognition;
    setListening(true);
  }, [listening]);

  const handleSubmit = () => {
    if (!draft.trim()) return;
    onTranscript(draft.trim());
    setDraft('');
  };

  const handleCorrect = (text: string) => {
    setDraft(text);
  };

  return (
    <div className="pw-voice">
      <button
        className={`pw-voice-btn ${listening ? 'pw-voice-listening' : ''}`}
        onClick={toggleListening}
        aria-label={listening ? 'Stop recording' : 'Start voice input'}
        title={listening ? 'Stop recording' : 'Voice input'}
      >
        {listening ? '⬤' : '🎤'}
      </button>
      <AnimatePresence>
        {draft && (
          <motion.div
            className="pw-voice-draft"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
          >
            <textarea
              className="pw-voice-textarea"
              value={draft}
              onChange={(e) => handleCorrect(e.target.value)}
              placeholder="Your speech will appear here. You can edit it or correct by voice."
              rows={3}
                          />
                          <div className="pw-voice-actions">
                            <button className="pw-voice-submit" onClick={handleSubmit}>Submit</button>
                            <button className="pw-voice-clear" onClick={() => setDraft('')}>Clear</button>
                            {HAS_TTS && draft.trim() && (
                              <button className="pw-voice-tts" onClick={() => speakText(draft)} title="Preview aloud">🔊</button>
                            )}
                            {listening && <span className="pw-voice-recording">Recording… speak now</span>}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {error && <p className="pw-voice-error">{error}</p>}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 9. INTEGRATED COMMAND + VOICE
// ═══════════════════════════════════════════════════════════════════

function IntegratedCommand() {
  const commandOpen = useLivingStore((s) => s.commandOpen);
  const setCommandOpen = useLivingStore((s) => s.setCommandOpen);
  const activeExecutions = useLivingStore((s) => s.activeExecutions);
  const observations = useLivingStore((s) => s.observations);
  const executeAction = useLivingStore((s) => s.executeAction);
  const fetchReality = useLivingStore((s) => s.fetchReality);
  const fetchLivingObjects = useLivingStore((s) => s.fetchLivingObjects);

  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (commandOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [commandOpen]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandOpen(true);
      }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [setCommandOpen]);

  const handleSubmit = () => {
    const val = input.trim();
    if (!val) return;
    setInput('');
    setCommandOpen(false);
    executeAction('outcome', {
      intent: val,
      data: {},
      label: val.length > 60 ? val.slice(0, 60) + '…' : val,
    }).then(() => {
      fetchReality();
      fetchLivingObjects();
    });
  };

  const handleVoiceTranscript = (text: string) => {
    setInput(text);
    setCommandOpen(true);
  };

  return (
    <div className="pw-command-zone">
      <div className="pw-command-bar">
        {commandOpen ? (
          <motion.div
            className="pw-command-expanded"
            initial={{ y: 4, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 4, opacity: 0 }}
          >
            <div className="pw-command-input-row">
              <span className="pw-command-prompt">→</span>
              <input
                ref={inputRef}
                type="text"
                className="pw-command-input"
                placeholder="Ask SHUNYA or type a command…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSubmit();
                  if (e.key === 'Escape') { setCommandOpen(false); setInput(''); }
                }}
              />
              <VoiceInput onTranscript={handleVoiceTranscript} />
            </div>
          </motion.div>
        ) : (
          <button className="pw-command-trigger" onClick={() => setCommandOpen(true)}>
            <span className="pw-command-trigger-icon">
              {activeExecutions.length > 0 ? '⟳' : '→'}
            </span>
            <span className="pw-command-trigger-text">
              {activeExecutions.length > 0
                ? `${activeExecutions.length} action${activeExecutions.length > 1 ? 's' : ''} in progress`
                : observations.length > 0
                ? `${observations.length} thing${observations.length > 1 ? 's' : ''} to discuss`
                : 'Ask SHUNYA or type a command…'}
            </span>
            <span className="pw-command-kbd">⌘K</span>
            <VoiceInput onTranscript={handleVoiceTranscript} />
          </button>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 10. MOBILE DOMAIN NAVIGATION
// ═══════════════════════════════════════════════════════════════════

function MobileDomainNav() {
  const [open, setOpen] = useState(false);

  const handleDomainClick = useCallback((domain: Domain) => {
    useWorkspaceStore.getState().open(domain.label, domain.wsType as any, {
      objectType: domain.id,
      objectId: domain.id,
    });
    setOpen(false);
  }, []);

  return (
    <div className="pw-mobile-nav">
      <button
        className="pw-mobile-nav-btn"
        onClick={() => setOpen(!open)}
        aria-label="Organization"
        title="Organization"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
          <line x1="3" y1="3" x2="15" y2="3" />
          <line x1="3" y1="9" x2="15" y2="9" />
          <line x1="3" y1="15" x2="15" y2="15" />
        </svg>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            className="pw-mobile-nav-panel"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <p className="pw-mobile-nav-title">Organization</p>
            {ORGANIZATIONAL_DOMAINS.map((domain) => (
              <button
                key={domain.id}
                className="pw-mobile-nav-item"
                onClick={() => handleDomainClick(domain)}
              >
                <span className="pw-mobile-nav-icon">{domain.icon}</span>
                <span>{domain.label}</span>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 11. PRIMARY FOCUS AREA
// ═══════════════════════════════════════════════════════════════════

function PrimaryFocusArea() {
  const calm = useLivingStore((s) => s.awarenessCalm);
  const activeExecutions = useLivingStore((s) => s.activeExecutions);
  const [intention, setIntention] = useState<string | null>(null);

  // Wire intention endpoint on mount
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('/api/v1/intention', { credentials: 'include' });
        const d = await r.json();
        if (d.success && d.explanation) {
          setIntention(d.explanation);
        }
      } catch { /* silent */ }
    })();
  }, []);

  const presenceMode: 'calm' | 'working' | 'attentive' | 'active' =
    activeExecutions.length > 0 ? 'working'
    : calm ? 'calm'
    : 'attentive';

  return (
    <div className="pw-focus">
      {/* Top bar */}
      <div className="pw-focus-top">
        <div className="pw-focus-brand">
          <span className="pw-focus-brand-icon">शून्य</span>
          <span className="pw-focus-brand-label">SHUNYA</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <PresenceIndicator mode={presenceMode} />
          {/* Mobile domain button */}
          <MobileDomainNav />
        </div>
      </div>

      {/* Intention — SHUNYA's recommendation */}
      {intention && (
        <motion.div
          className="pw-intention"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <span className="pw-intention-label">SHUNYA suggests: </span>
          <span className="pw-intention-text">{intention}</span>
        </motion.div>
      )}

      {/* Companion greeting */}
      <CompanionGreeting />

      {/* What matters now */}
      <WhatMattersNow />

      {/* Work visibility */}
      <WorkVisibility />

      {/* Narrative stream */}
      <NarrativeStream />

      {/* Calm state */}
      {calm && <CalmState />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 11. DOMAIN OVERVIEW — Truthful domain concept surface
// ═══════════════════════════════════════════════════════════════════

function DomainOverview({ domain }: { domain: Domain }) {
  const [data, setData] = useState<{ count?: number; status?: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    (async () => {
      try {
        const resp = await fetch(`/api/v1/objects/types`, { credentials: 'include' });
        const json = await resp.json();
        const types = json.data || {};
        const count = types[domain.id] || 0;
        setData({ count });
      } catch {
        setData({});
      }
      setLoading(false);
    })();
  }, [domain.id]);

  return (
    <div className="pw-domain-overview">
      <div className="pw-domain-header">
        <span className="pw-domain-icon">{domain.icon}</span>
        <h2 className="pw-domain-title">{domain.label}</h2>
      </div>
      <p className="pw-domain-desc">{domain.description}</p>

      {loading && <div className="pw-domain-loading">Checking available data…</div>}

      {!loading && (
        <>
          {data?.count && data.count > 0 ? (
            <p className="pw-domain-data">{data.count} item{data.count > 1 ? 's' : ''} currently available.</p>
          ) : (
            <div className="pw-domain-empty">
              <p>This area is set up in SHUNYA but no data exists yet.</p>
              <p className="pw-domain-empty-hint">
                {domain.id === 'finance' && 'Financial tracking is planned. Ask SHUNYA to record financial information.'}
                {domain.id === 'commercial' && 'Commercial capability (G4) exists. Data will appear as relationships and opportunities are created.'}
                {domain.id === 'marketing' && 'Marketing capability (G5) exists. Campaigns and growth intelligence will appear here.'}
                {domain.id === 'sales' && 'Sales bridges to commercial execution. Pipeline will appear as opportunities are created.'}
                {domain.id === 'operations' && 'Operations tracking is planned. Connect systems to populate operational data.'}
                {domain.id === 'knowledge' && 'Knowledge objects will appear here as documents and references are added.'}
                {domain.id === 'outputs' && 'Outputs from SHUNYA work will appear here once work is completed.'}
                {domain.id === 'memory' && 'SHUNYA remembers your organization permanently. Memory features are being built.'}
                {domain.id === 'relationships' && 'Relationship graph capability exists. Data will appear as relationships are identified.'}
                {(domain.id === 'finance' || domain.id === 'operations') && ' This capability is not yet implemented.'}
              </p>
            </div>
          )}

          <div className="pw-domain-actions">
            <p className="pw-domain-actions-label">What you can do:</p>
            <button className="pw-domain-action" onClick={() => useWorkspaceStore.getState().open('Ask SHUNYA', 'home')}>
              Ask SHUNYA about {domain.label.toLowerCase()}
            </button>
            <button className="pw-domain-action pw-domain-action-back" onClick={() => {
              // Close current workspace and go back to focus
              const active = useWorkspaceStore.getState().workspaces.find(
                w => w.identity.type === 'object' && w.identity.objectType === domain.id
              );
              if (active) useWorkspaceStore.getState().close(active.identity.id);
            }}>
              Back to focus
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 12. DOMAIN WORKSPACE ROUTER — Routes every workspace type
// ═══════════════════════════════════════════════════════════════════

const DOMAIN_IDS = new Set(ORGANIZATIONAL_DOMAINS.map(d => d.id));

function DomainWorkspaceRouter() {
  const active = useActiveWorkspace();

  // No active workspace → show focus
  if (!active) return <PrimaryFocusArea />;

  // Loading state
  if (active.status === 'loading' || active.status === 'creating') {
    return (
      <div className="pw-loading">
        <div className="pw-loading-shimmer" />
        <p className="pw-loading-text">Opening {active.identity.name}…</p>
      </div>
    );
  }

  // Error state
  if (active.status === 'error') {
    return (
      <div className="pw-error" role="alert">
        <p className="pw-error-title">Could not open</p>
        <p className="pw-error-msg">{active.error || 'Unknown error'}</p>
        <button className="pw-error-retry" onClick={() => {
          useWorkspaceStore.getState().transitionTo(active.identity.id, 'loading');
        }}>Retry</button>
      </div>
    );
  }

  // Home workspace → show focus area
  if (active.identity.type === 'home') {
    return <PrimaryFocusArea />;
  }

  // ── Type-based routing ──

  // People panel — Organization Browser with hierarchy, search, roles
  if (active.identity.type === 'people') {
    return <div className="pw-panel-container"><OrganizationBrowser /></div>;
  }

  // Admin panel
  if (active.identity.type === 'admin') {
    return <div className="pw-panel-container"><AdminPanel /></div>;
  }

  // Import/Export panel
  if (active.identity.type === 'import-export') {
    return <div className="pw-panel-container"><ImportExportPanel /></div>;
  }

  // Commitment workspace — self-contained, reads from API
  if (active.identity.type === 'commitment') {
    return (
      <div className="pw-panel-container">
        <CommitmentWorkspace />
      </div>
    );
  }

  // Conversation workspace
  if (active.identity.type === 'conversation') {
    return (
      <div className="pw-panel-container">
        <ConversationWorkspace
          conversation={active.identity.objectId ? {
            id: active.identity.objectId,
            title: active.identity.name,
            intent: '',
            status: 'active',
            participants: [],
            objectIds: [],
            commitmentIds: [],
          } : undefined}
        />
      </div>
    );
  }

  // Object workspace
  if (active.identity.type === 'object' && active.identity.objectId) {
    // Commercial — real workspace with opportunities and proposals
    if (active.identity.objectId === 'commercial') {
      return <div className="pw-panel-container"><CommercialWorkspace /></div>;
    }
    // Relationships — real workspace with relationships, timeline, memory
    if (active.identity.objectId === 'relationships') {
      return <div className="pw-panel-container"><RelationshipWorkspace /></div>;
    }
    // Marketing — real campaign browser
    if (active.identity.objectId === 'marketing') {
      return <div className="pw-panel-container"><MarketingWorkspace /></div>;
    }
    // Sales — real pipeline viewer
    if (active.identity.objectId === 'sales') {
      return <div className="pw-panel-container"><SalesPipeline /></div>;
    }
    // Leads — management
    if (active.identity.objectId === 'leads') {
      return <div className="pw-panel-container"><LeadManagement /></div>;
    }
    // Work — execution visibility
    if (active.identity.objectId === 'work') {
      return <div className="pw-panel-container"><ExecutionWorkspace /></div>;
    }
    // Outputs — artifact discovery
    if (active.identity.objectId === 'outputs') {
      return <div className="pw-panel-container"><OutputsBrowser /></div>;
    }
    // If the objectId is a domain concept (finance, marketing, etc.), show domain overview
    if (DOMAIN_IDS.has(active.identity.objectId) && !active.identity.objectType?.includes('_')) {
      const domain = ORGANIZATIONAL_DOMAINS.find(d => d.id === active.identity.objectId);
      if (domain) {
        return (
          <div className="pw-panel-container">
            <DomainOverview domain={domain} />
          </div>
        );
      }
    }
    // Otherwise render real object workspace
    return (
      <div className="pw-object-workspace">
        <ObjectWorkspaceViewer
          objectId={active.identity.objectId}
          objectType={active.identity.objectType || active.identity.objectId}
        />
      </div>
    );
  }

  // Fallback to focus area
  return <PrimaryFocusArea />;
}

// ═══════════════════════════════════════════════════════════════════
// 13. MAIN EXPORT — Routes workspaces + shows organization sidebar
// ═══════════════════════════════════════════════════════════════════

export function PrimaryWorkspace({ loading: _loading }: { loading?: boolean }) {
  const [arrivalDone, setArrivalDone] = useState(false);
  const [orgCollapsed, setOrgCollapsed] = useState(false);
  const startPolling = useLivingStore((s) => s.startPolling);

  useEffect(() => {
    const stop = startPolling();
    const sse = subscribeSSE('reality');
    return () => { stop(); sse.close(); };
  }, [startPolling]);

  return (
    <div className="pw-workspace">
      {!arrivalDone && <ArrivalWordmark onDone={() => setArrivalDone(true)} />}

      {/* FOCUS + WORLD layout */}
      <div className="pw-layout">
        {/* WORLD — Organizational Orientation */}
        <OrganizationalOrientation
          collapsed={orgCollapsed}
          onToggle={() => setOrgCollapsed(!orgCollapsed)}
        />

        {/* CENTER — DomainWorkspaceRouter handles ALL workspace types */}
        <main className="pw-layout-center" role="main">
          <DomainWorkspaceRouter />
        </main>
      </div>

      {/* Command + Voice — always at bottom */}
      <IntegratedCommand />
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 12. ARRIVAL WORDMARK
// ═══════════════════════════════════════════════════════════════════

function ArrivalWordmark({ onDone }: { onDone: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDone, 800);
    return () => clearTimeout(t);
  }, [onDone]);

  return (
    <motion.div
      className="pw-arrival"
      initial={{ opacity: 1 }}
      animate={{ opacity: 0 }}
      transition={{ duration: 0.6, delay: 0.6 }}
    >
      <motion.span
        className="pw-arrival-text"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
      >
        शून्य
      </motion.span>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// STYLES
// ═══════════════════════════════════════════════════════════════════

const styles = document.createElement('style');
styles.textContent = `
/* ── Workspace Shell ──────────────────────────────────────── */
.pw-workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--shunya-bg, #FBF8F5);
  color: var(--shunya-text, #1A1C1D);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
}
.pw-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.pw-layout-center {
  flex: 1;
  overflow-y: auto;
  min-width: 0;
}
.pw-object-workspace {
  height: 100vh;
  overflow: hidden;
}

/* ── Arrival ──────────────────────────────────────────────── */
.pw-arrival {
  position: fixed; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--shunya-bg, #FBF8F5);
  z-index: 100;
  pointer-events: none;
}
.pw-arrival-text {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: clamp(2rem, 6vw, 3.5rem);
  font-weight: 300;
  color: var(--shunya-text, #1A1C1D);
  letter-spacing: 0.06em;
}

/* ── Focus Area ───────────────────────────────────────────── */
.pw-focus {
  display: flex;
  flex-direction: column;
  padding: 40px 48px;
  max-width: 720px;
  min-height: 100%;
}
.pw-focus-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 28px;
}
.pw-focus-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pw-focus-brand-icon {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: 18px;
  font-weight: 400;
  color: var(--shunya-text, #1A1C1D);
  letter-spacing: 0.06em;
}
.pw-focus-brand-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

/* ── Presence ─────────────────────────────────────────────── */
.pw-presence {
  display: flex;
  align-items: center;
  gap: 8px;
}
.pw-presence-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.pw-presence-label {
  font-size: 12px; font-weight: 400;
  color: rgba(26,28,29,0.55);
  letter-spacing: 0.03em;
}

/* ── Greeting ─────────────────────────────────────────────── */
.pw-greeting { margin-bottom: 20px; }
.pw-greeting-text {
  font-size: 15px; font-weight: 400;
  color: rgba(26,28,29,0.65);
  line-height: 1.5; margin: 0;
}

/* ── Attention ────────────────────────────────────────────── */
.pw-attention {
  background: var(--shunya-surface, #ffffff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}
.pw-attention-critical { border-left: 3px solid #c0392b; }
.pw-attention-high { border-left: 3px solid #e67e22; }
.pw-attention-normal { border-left: 3px solid #6a9f6a; }
.pw-attention-low { border-left: 3px solid transparent; }
.pw-attention-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
}
.pw-attention-priority {
  font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
}
.pw-attention-critical .pw-attention-priority { color: #c0392b; }
.pw-attention-high .pw-attention-priority { color: #e67e22; }
.pw-attention-normal .pw-attention-priority { color: #6a9f6a; }
.pw-attention-count { font-size: 11px; color: rgba(26,28,29,0.45); }
.pw-attention-title {
  font-size: 18px; font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
  margin: 0 0 8px; line-height: 1.3;
}
.pw-attention-reason {
  font-size: 14px; color: rgba(26,28,29,0.7);
  margin: 0 0 6px; line-height: 1.5;
}
.pw-attention-why {
  font-size: 13px; color: rgba(26,28,29,0.55);
  margin: 0 0 4px; font-style: italic;
}
.pw-attention-action {
  font-size: 13px; color: var(--shunya-gold, #a4865f);
  margin: 0 0 16px;
}
.pw-attention-actions {
  display: flex; gap: 8px; flex-wrap: wrap;
}
.pw-attention-btn {
  font-size: 12px; padding: 6px 16px; border-radius: 6px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  background: transparent; color: var(--shunya-text, #1A1C1D);
  cursor: pointer; transition: all 0.15s;
}
.pw-attention-btn:hover { border-color: var(--shunya-gold, #a4865f); }
.pw-attention-btn-primary {
  background: var(--shunya-gold, #a4865f); color: #fff;
  border-color: var(--shunya-gold, #a4865f);
}
.pw-attention-btn-primary:hover { opacity: 0.85; }
.pw-attention-btn-ghost { border-color: transparent; color: rgba(26,28,29,0.45); }

/* ── Narrative ────────────────────────────────────────────── */
.pw-narrative { margin-bottom: 20px; }
.pw-narrative-header { margin-bottom: 8px; }
.pw-narrative-label {
  font-size: 12px; font-weight: 500; color: rgba(26,28,29,0.4);
  text-transform: uppercase; letter-spacing: 0.06em;
}
.pw-narrative-items { display: flex; flex-direction: column; gap: 4px; }
.pw-narrative-item {
  display: flex; gap: 10px; padding: 8px 0; align-items: flex-start;
}
.pw-narrative-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: rgba(26,28,29,0.2); margin-top: 5px; flex-shrink: 0;
}
.pw-narrative-dot-important { background: #e67e22; }
.pw-narrative-body { display: flex; flex-direction: column; gap: 2px; }
.pw-narrative-text {
  font-size: 13px; color: var(--shunya-text, #1A1C1D); line-height: 1.4;
}
.pw-narrative-detail { font-size: 12px; color: rgba(26,28,29,0.55); }
.pw-narrative-time { font-size: 11px; color: rgba(26,28,29,0.35); }
.pw-narrative-empty {
  font-size: 13px; color: rgba(26,28,29,0.45); font-style: italic;
}

/* ── Calm State ───────────────────────────────────────────── */
.pw-calm {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  text-align: center; padding: 60px 40px; gap: 12px;
  flex: 1;
}
.pw-calm-brand {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: 28px; font-weight: 300;
  color: var(--shunya-text, #1A1C1D);
  opacity: 0.2; letter-spacing: 0.06em;
}
.pw-calm-text {
  font-size: 14px; color: rgba(26,28,29,0.55);
  max-width: 380px; line-height: 1.6; margin: 0;
}
.pw-calm-action {
  font-size: 13px; color: var(--shunya-gold, #a4865f);
  margin: 0;
}
.pw-calm-updated { font-size: 11px; color: rgba(26,28,29,0.3); }

/* ── Work Visibility ──────────────────────────────────────── */
.pw-work {
  margin-bottom: 20px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 8px;
  overflow: hidden;
}
.pw-work-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}
.pw-work-header:hover { background: rgba(26,28,29,0.02); }
.pw-work-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(26,28,29,0.55);
}
.pw-work-toggle {
  font-size: 10px;
  color: rgba(26,28,29,0.3);
}
.pw-work-items {
  border-top: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  padding: 8px 0;
}
.pw-work-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  font-size: 13px;
}
.pw-work-status {
  width: 16px;
  text-align: center;
  flex-shrink: 0;
}
.pw-work-text {
  flex: 1;
  color: var(--shunya-text, #1A1C1D);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pw-work-owner {
  font-size: 11px;
  color: rgba(26,28,29,0.45);
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(26,28,29,0.04);
  flex-shrink: 0;
}
.pw-work-time {
  font-size: 11px;
  color: rgba(26,28,29,0.3);
  flex-shrink: 0;
}
.pw-work-track {
  width: 60px;
  height: 3px;
  background: rgba(26,28,29,0.08);
  border-radius: 2px;
  overflow: hidden;
  flex-shrink: 0;
}
.pw-work-fill {
  display: block;
  height: 100%;
  border-radius: 2px;
  background: var(--shunya-gold, #a4865f);
}

/* ── Organizational Orientation ───────────────────────────── */
.pw-org-orientation {
  width: 260px;
  min-width: 0;
  overflow: hidden;
  border-right: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  display: flex;
  flex-direction: column;
  background: var(--shunya-surface-subtle, #f8f7f4);
}
.pw-org-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 8px;
  flex-shrink: 0;
}
.pw-org-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--shunya-text, #1A1C1D);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.pw-org-toggle {
  background: transparent;
  border: none;
  color: rgba(26,28,29,0.35);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}
.pw-org-toggle:hover { color: var(--shunya-text, #1A1C1D); }
.pw-org-hint {
  font-size: 11px;
  color: rgba(26,28,29,0.35);
  padding: 0 16px 8px;
  margin: 0;
}
.pw-org-domains {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}
.pw-org-domain {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--shunya-text, #1A1C1D);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
  font-family: inherit;
}
.pw-org-domain:hover {
  background: rgba(26,28,29,0.04);
}
.pw-org-domain-icon {
  font-size: 14px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
  opacity: 0.7;
}
.pw-org-domain-label {
  flex: 1;
}
.pw-org-domain-count {
  font-size: 11px;
  color: rgba(26,28,29,0.35);
  background: rgba(26,28,29,0.06);
  padding: 1px 6px;
  border-radius: 8px;
}
.pw-org-footer {
  font-size: 10px;
  color: rgba(26,28,29,0.3);
  padding: 12px 16px;
  margin: 0;
  text-align: center;
  flex-shrink: 0;
  border-top: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}

/* ── Command Zone ─────────────────────────────────────────── */
.pw-command-zone {
  border-top: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  padding: 8px 16px;
  background: var(--shunya-bg, #FBF8F5);
  flex-shrink: 0;
}
.pw-command-bar { }
.pw-command-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 10px;
  background: var(--shunya-surface, #ffffff);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  color: var(--shunya-text, #1A1C1D);
  font: inherit;
}
.pw-command-trigger:hover {
  border-color: var(--shunya-gold, #a4865f);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.pw-command-trigger-icon {
  font-size: 14px;
  color: var(--shunya-gold, #a4865f);
  flex-shrink: 0;
}
.pw-command-trigger-text {
  flex: 1;
  font-size: 13px;
  color: rgba(26,28,29,0.45);
}
.pw-command-kbd {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 4px;
  color: rgba(26,28,29,0.35);
  flex-shrink: 0;
}
.pw-command-expanded {
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 10px;
  background: var(--shunya-surface, #ffffff);
  padding: 8px 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
}
.pw-command-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pw-command-prompt {
  font-size: 16px;
  color: var(--shunya-gold, #a4865f);
  flex-shrink: 0;
}
.pw-command-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  font-family: inherit;
  background: transparent;
  color: var(--shunya-text, #1A1C1D);
  padding: 6px 0;
}
.pw-command-input::placeholder { color: rgba(26,28,29,0.3); }

/* ── Voice Input ──────────────────────────────────────────── */
.pw-voice {
  position: relative;
  flex-shrink: 0;
}
.pw-voice-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.2s;
}
.pw-voice-btn:hover {
  border-color: var(--shunya-gold, #a4865f);
  background: rgba(164,134,95,0.06);
}
.pw-voice-listening {
  border-color: #c0392b;
  background: rgba(192,57,43,0.06);
  animation: pulse-ring 1.5s infinite;
}
@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(192,57,43,0.3); }
  50% { box-shadow: 0 0 0 6px rgba(192,57,43,0); }
  100% { box-shadow: 0 0 0 0 rgba(192,57,43,0); }
}
.pw-voice-draft {
  position: absolute;
  bottom: 44px;
  right: 0;
  width: 320px;
  background: var(--shunya-surface, #ffffff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
  z-index: 50;
}
.pw-voice-textarea {
  width: 100%;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 6px;
  padding: 8px;
  font-size: 13px;
  font-family: inherit;
  resize: none;
  outline: none;
  color: var(--shunya-text, #1A1C1D);
  background: var(--shunya-surface-subtle, #f8f7f4);
}
.pw-voice-textarea:focus {
  border-color: var(--shunya-gold, #a4865f);
}
.pw-voice-actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  align-items: center;
}
.pw-voice-submit {
  padding: 4px 14px;
  border-radius: 6px;
  border: none;
  background: var(--shunya-gold, #a4865f);
  color: #fff;
  font-size: 12px;
  cursor: pointer;
}
.pw-voice-clear {
  padding: 4px 14px;
  border-radius: 6px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  background: transparent;
  color: rgba(26,28,29,0.55);
  font-size: 12px;
  cursor: pointer;
}
.pw-voice-recording {
  font-size: 11px;
  color: #c0392b;
  margin-left: auto;
}
.pw-voice-error {
  font-size: 11px;
  color: #c0392b;
  margin-top: 4px;
}

/* ── Domain Overview ──────────────────────────────────────── */
.pw-panel-container {
  padding: 40px 48px;
  max-width: 720px;
}
.pw-domain-overview { }
.pw-domain-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.pw-domain-icon {
  font-size: 24px;
  flex-shrink: 0;
}
.pw-domain-title {
  font-size: 22px;
  font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
  margin: 0;
}
.pw-domain-desc {
  font-size: 14px;
  color: rgba(26,28,29,0.55);
  margin: 0 0 24px;
}
.pw-domain-loading {
  font-size: 13px;
  color: rgba(26,28,29,0.45);
  font-style: italic;
}
.pw-domain-data {
  font-size: 14px;
  color: var(--shunya-text, #1A1C1D);
  margin-bottom: 24px;
}
.pw-domain-empty {
  background: var(--shunya-surface, #ffffff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 24px;
}
.pw-domain-empty p {
  font-size: 14px;
  color: rgba(26,28,29,0.65);
  margin: 0 0 8px;
  line-height: 1.5;
}
.pw-domain-empty-hint {
  font-size: 13px;
  color: rgba(26,28,29,0.45);
  font-style: italic;
}
.pw-domain-actions { }
.pw-domain-actions-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(26,28,29,0.55);
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.pw-domain-action {
  display: block;
  width: 100%;
  padding: 10px 16px;
  margin-bottom: 6px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 8px;
  background: var(--shunya-surface, #ffffff);
  color: var(--shunya-text, #1A1C1D);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  font-family: inherit;
}
.pw-domain-action:hover {
  border-color: var(--shunya-gold, #a4865f);
}
.pw-domain-action-back {
  color: rgba(26,28,29,0.55);
  font-size: 12px;
}

/* ── Intention ────────────────────────────────────────────── */
.pw-intention {
  margin-bottom: 16px;
  padding: 10px 16px;
  background: rgba(164,134,95,0.06);
  border: 1px solid rgba(164,134,95,0.15);
  border-radius: 8px;
  display: flex;
  align-items: flex-start;
  gap: 6px;
}
.pw-intention-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--shunya-gold, #a4865f);
  white-space: nowrap;
  flex-shrink: 0;
}
.pw-intention-text {
  font-size: 13px;
  color: rgba(26,28,29,0.65);
  line-height: 1.4;
}

/* ── Mobile Domain Navigation ───────────────────────────── */
.pw-mobile-nav {
  display: none;
  position: relative;
}
.pw-mobile-nav-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(26,28,29,0.55);
  transition: all 0.15s;
}
.pw-mobile-nav-btn:hover {
  border-color: var(--shunya-gold, #a4865f);
  color: var(--shunya-text, #1A1C1D);
}
.pw-mobile-nav-panel {
  position: absolute;
  top: 40px;
  right: 0;
  width: 240px;
  background: var(--shunya-surface, #ffffff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
  z-index: 50;
}
.pw-mobile-nav-title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(26,28,29,0.4);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0 0 8px;
  padding: 0 4px;
}
.pw-mobile-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 8px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--shunya-text, #1A1C1D);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: background 0.15s;
}
.pw-mobile-nav-item:hover {
  background: rgba(26,28,29,0.04);
}
.pw-mobile-nav-icon {
  font-size: 14px;
  width: 20px;
  text-align: center;
  opacity: 0.7;
}

/* ── Commercial / Relationship List Items ────────────────── */
.pw-commercial-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.pw-commercial-item {
  padding: 12px 16px;
  background: var(--shunya-surface, #ffffff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 8px;
  transition: border-color 0.15s;
}
.pw-commercial-item:hover {
  border-color: var(--shunya-gold, #a4865f);
}
.pw-commercial-item-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
  margin-bottom: 4px;
}
.pw-commercial-item-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
}
.pw-commercial-tag {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 4px;
  background: rgba(26,28,29,0.04);
  color: rgba(26,28,29,0.55);
}
.pw-status-sent { color: #e67e22; }
.pw-status-accepted { color: #6a9f6a; }
.pw-status-active { color: #6a9f6a; }
.pw-status-lead { color: #a4865f; }
.pw-commercial-date {
  font-size: 11px;
  color: rgba(26,28,29,0.35);
}
.pw-tab-btn {
  padding: 6px 16px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 6px;
  background: transparent;
  color: rgba(26,28,29,0.55);
  font-size: 12px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}
.pw-tab-btn:hover {
  border-color: var(--shunya-gold, #a4865f);
}
.pw-tab-active {
  background: var(--shunya-gold, #a4865f);
  color: #fff;
  border-color: var(--shunya-gold, #a4865f);
}

/* ── Relationship Detail ───────────────────────────────── */
.pw-rel-detail {
  padding: 8px 16px 16px;
  margin: 0 0 4px;
  background: var(--shunya-surface-subtle, #f8f7f4);
  border-radius: 0 0 8px 8px;
}
.pw-rel-section {
  margin-bottom: 12px;
}
.pw-rel-section-title {
  font-size: 12px;
  font-weight: 500;
  color: rgba(26,28,29,0.55);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0 0 8px;
}
.pw-rel-timeline-item {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  align-items: flex-start;
}
.pw-rel-tl-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(26,28,29,0.2);
  margin-top: 5px;
  flex-shrink: 0;
}
.pw-rel-tl-text {
  font-size: 13px;
  color: var(--shunya-text, #1A1C1D);
  margin: 0;
  line-height: 1.4;
}
.pw-rel-memory {
  padding: 12px;
  background: var(--shunya-surface, #ffffff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 6px;
}
.pw-rel-memory p {
  font-size: 13px;
  color: rgba(26,28,29,0.65);
  margin: 0 0 4px;
}

/* ── Loading / Error States ───────────────────────────────── */
.pw-loading {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 40px 48px;
}
.pw-loading-shimmer {
  height: 3px;
  background: linear-gradient(90deg, var(--shunya-border, rgba(26,28,29,0.07)) 0%, var(--shunya-gold, #a4865f) 50%, var(--shunya-border, rgba(26,28,29,0.07)) 100%);
  background-size: 200% 100%;
  animation: pw-shimmer 1.5s infinite;
  border-radius: 2px;
}
@keyframes pw-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.pw-loading-text {
  font-size: 13px;
  color: rgba(26,28,29,0.45);
}
.pw-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 40px;
  text-align: center;
}
.pw-error-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
  margin: 0;
}
.pw-error-msg {
  font-size: 13px;
  color: rgba(26,28,29,0.55);
  margin: 0;
  max-width: 400px;
}
.pw-error-retry {
  padding: 6px 20px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 6px;
  background: var(--shunya-surface, #ffffff);
  color: var(--shunya-text, #1A1C1D);
  font-size: 12px;
  cursor: pointer;
  font-family: inherit;
}
.pw-error-retry:hover { border-color: var(--shunya-gold, #a4865f); }

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 768px) {
  .pw-org-orientation { display: none; }
  .pw-mobile-nav { display: block; }
  .pw-focus { padding: 24px 20px; }
  .pw-panel-container { padding: 24px 20px; }
  .pw-voice-draft { width: calc(100vw - 40px); right: -8px; }
}
`;
styles.id = 'pw-workspace-styles';
if (typeof document !== 'undefined' && !document.getElementById('pw-workspace-styles')) {
  document.head.appendChild(styles);
}