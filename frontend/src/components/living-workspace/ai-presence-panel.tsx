/**
 * SHUNYA LX-02A — Continuous Companion
 *
 * Not a chatbot. Not a dashboard. Not an automation tool.
 * A continuously present operating partner that speaks in first person,
 * references its own work, and makes the founder feel they are working
 * with someone rather than using software.
 *
 * Every view answers four questions without requiring interaction:
 *   What has SHUNYA already done?
 *   What is SHUNYA doing now?
 *   What is SHUNYA waiting for?
 *   What does SHUNYA recommend next?
 */

import { useState, useEffect, useRef, type FC } from 'react';
import { motion } from 'framer-motion';
import { useLivingStore } from './living-store';
import { MemoryReview } from './memory-review';
import type { AIObservation, AIRecommendation, Execution } from './types';

// ── Helpers ────────────────────────────────────────────────────────

function confidenceLabel(c: number): string {
  if (c >= 0.85) return 'High confidence';
  if (c >= 0.7) return 'Moderate confidence';
  if (c >= 0.5) return 'Some confidence';
  return 'Low confidence';
}

function timeToBusinessNarrative(ts: string | null | undefined): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (mins < 2) return 'just moments ago';
    if (mins < 5) return 'a few minutes ago';
    if (mins < 60) return `${mins} minutes ago`;
    if (hours === 1) return 'about an hour ago';
    if (hours < 24) return `${hours} hours ago`;
    if (days === 1) return 'yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    return `${Math.floor(days / 30)} months ago`;
  } catch {
    return '';
  }
}

// ── What Has SHUNYA Already Done? ──────────────────────────────────

const WhatHasBeenDone: FC<{
  observations: AIObservation[];
  executionHistory: Execution[];
  realityEventCount: number;
}> = ({ observations, executionHistory, realityEventCount }) => {
  const recentHistory = executionHistory.slice(-3).reverse();
  const hasWork = recentHistory.length > 0 || observations.length > 0;

  if (!hasWork) {
    return (
      <div className="lw-companion-section">
        <p className="lw-companion-narrative">
          I've been observing your organisation since you last signed in.
          No significant changes yet — I'll let you know when something
          deserves your attention.
        </p>
      </div>
    );
  }

  return (
    <div className="lw-companion-section">
      {recentHistory.length > 0 && (
        <p className="lw-companion-narrative">
          {recentHistory.length === 1
            ? `I completed one task ${timeToBusinessNarrative(recentHistory[0].completed_at)}.`
            : `I completed ${recentHistory.length} tasks since your last visit.`}
          {observations.length > 0 &&
            ` I've also observed ${observations.length} thing${observations.length !== 1 ? 's' : ''} that may interest you.`}
        </p>
      )}
      {recentHistory.length === 0 && observations.length > 0 && (
        <p className="lw-companion-narrative">
          While you were away, I noticed {observations.length} change{observations.length !== 1 ? 's' : ''}
          {realityEventCount > 0 ? ` across ${realityEventCount} event${realityEventCount !== 1 ? 's' : ''}` : ''}.
        </p>
      )}
      {recentHistory.length > 0 && (
        <div className="lw-companion-done-list">
          {recentHistory.map((exec) => (
            <div key={exec.id} className="lw-companion-done-item">
              <span className="lw-companion-done-check">✓</span>
              <span className="lw-companion-done-label">{exec.label}</span>
              {exec.outcome && <span className="lw-companion-done-outcome">— {exec.outcome}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── What Is SHUNYA Doing Now? ──────────────────────────────────────

const WhatIsHappeningNow: FC<{ executions: Execution[] }> = ({ executions }) => {
  if (executions.length === 0) {
    return (
      <div className="lw-companion-section">
        <p className="lw-companion-narrative lw-companion-quiet">
          I'm currently monitoring your organisation for changes.
        </p>
      </div>
    );
  }

  return (
    <div className="lw-companion-section">
      <p className="lw-companion-narrative">
        I'm working on {executions.length} thing{executions.length !== 1 ? 's' : ''} right now:
      </p>
      <div className="lw-companion-doing-list">
        {executions.map((exec) => (
          <motion.div
            key={exec.id}
            className="lw-companion-doing-item"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <span className="lw-companion-doing-spinner">⟳</span>
            <div className="lw-companion-doing-body">
              <span className="lw-companion-doing-label">{exec.label}</span>
              <div className="lw-companion-doing-track">
                <motion.div
                  className="lw-companion-doing-fill"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.round(exec.progress * 100)}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                />
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// ── What Is SHUNYA Waiting For? ────────────────────────────────────

const WhatIsBeingMonitored: FC<{ observations: AIObservation[] }> = ({ observations }) => {
  if (observations.length === 0) {
    return null;
  }

  const monitoringPhrases: string[] = [];
  for (const obs of observations.slice(0, 3)) {
    const label = obs.title.replace(/^(Observation|Insight):\s*/i, '');
    monitoringPhrases.push(label);
  }

  return (
    <div className="lw-companion-section">
      <p className="lw-companion-narrative">
        I'm keeping an eye on:
      </p>
      <div className="lw-companion-monitoring">
        {monitoringPhrases.map((phrase, i) => (
          <div key={i} className="lw-companion-monitor-item">
            <span className="lw-companion-monitor-dot">·</span>
            <span className="lw-companion-monitor-text">{phrase}</span>
          </div>
        ))}
        {observations.length > 3 && (
          <div className="lw-companion-monitor-item">
            <span className="lw-companion-monitor-dot">·</span>
            <span className="lw-companion-monitor-text">and {observations.length - 3} more observation{observations.length - 3 !== 1 ? 's' : ''}</span>
          </div>
        )}
      </div>
    </div>
  );
};

// ── What Should Happen Next? ───────────────────────────────────────

const PreparedActionCountdown: FC<{
  rec: AIRecommendation;
  onExecute: () => void;
  onStop: () => void;
}> = ({ rec, onExecute, onStop }) => {
  const [countdown, setCountdown] = useState(10);
  const [hasExpired, setHasExpired] = useState(false);
  const executedRef = useRef(false);

  useEffect(() => {
    if (countdown <= 0 && !executedRef.current) {
      executedRef.current = true;
      setHasExpired(true);
      onExecute();
      return;
    }
    const timer = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown, onExecute]);

  return (
    <motion.div
      className="lw-companion-prepared"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="lw-companion-prepared-header">
        <span className="lw-companion-prepared-icon">⟳</span>
        <span className="lw-companion-prepared-label">I've prepared this action:</span>
      </div>
      <p className="lw-companion-prepared-title">{rec.title}</p>
      {!hasExpired ? (
        <>
          <p className="lw-companion-prepared-note">
            Executing in <strong>{countdown}</strong> second{countdown !== 1 ? 's' : ''} unless you stop me.
          </p>
          <div className="lw-companion-prepared-actions">
            <motion.button
              className="lw-companion-rec-btn lw-companion-rec-btn-primary"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => { if (!executedRef.current) { executedRef.current = true; setHasExpired(true); onExecute(); } }}
            >
              Execute now
            </motion.button>
            <motion.button
              className="lw-companion-rec-btn lw-companion-rec-btn-alt"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => { if (!executedRef.current) { executedRef.current = true; onStop(); } }}
            >
              Stop — I'll decide
            </motion.button>
          </div>
          <div className="lw-companion-countdown-track">
            <motion.div
              className="lw-companion-countdown-fill"
              initial={{ width: '100%' }}
              animate={{ width: '0%' }}
              transition={{ duration: 10, ease: 'linear' }}
            />
          </div>
        </>
      ) : (
        <p className="lw-companion-prepared-done">Action sent. I'll keep you updated on progress.</p>
      )}
    </motion.div>
  );
};

const WhatHappensNext: FC<{
  recommendations: AIRecommendation[];
  onExecute: (rec: AIRecommendation) => void;
  onDismiss: (id: string) => void;
}> = ({ recommendations, onExecute, onDismiss }) => {
  if (recommendations.length === 0) {
    return (
      <div className="lw-companion-section">
        <p className="lw-companion-narrative lw-companion-quiet">
          Nothing urgent right now. I'll keep watching and let you know
          when something changes.
        </p>
      </div>
    );
  }

  const top = recommendations[0];
  const others = recommendations.slice(1);

  // If confidence >= 0.85 and urgency is 'now', show prepared action
  if (top.confidence >= 0.85 && top.urgency === 'now') {
    return (
      <div className="lw-companion-section">
        <PreparedActionCountdown
          rec={top}
          onExecute={() => onExecute(top)}
          onStop={() => onDismiss(top.id)}
        />
      </div>
    );
  }

  return (
    <div className="lw-companion-section">
      <p className="lw-companion-narrative">
        Based on what I've been monitoring, I recommend we focus on:
      </p>

      {/* Top recommendation — fully explained */}
      <motion.div
        className="lw-companion-rec-top"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        <div className="lw-companion-rec-title">{top.title}</div>
        <div className="lw-companion-rec-exp">
          <div className="lw-companion-rec-question">Why this?</div>
          <p className="lw-companion-rec-answer">{top.description}</p>
        </div>
        <div className="lw-companion-rec-exp">
          <div className="lw-companion-rec-question">Why now?</div>
          <p className="lw-companion-rec-answer">
            {top.urgency === 'now'
              ? 'This requires immediate attention to avoid impact.'
              : top.urgency === 'today'
              ? 'Addressing this today keeps everything on track.'
              : 'This week is a reasonable timeframe for this.'}
          </p>
        </div>
        <div className="lw-companion-rec-exp">
          <div className="lw-companion-rec-question">What happens if we wait?</div>
          <p className="lw-companion-rec-answer">
            {top.urgency === 'now'
              ? 'Delaying beyond the next few hours may reduce effectiveness.'
              : top.urgency === 'today'
              ? 'Waiting until tomorrow is acceptable but this is time-sensitive.'
              : 'No immediate risk — but acting sooner keeps momentum.'}
          </p>
        </div>
        <div className="lw-companion-rec-exp">
          <div className="lw-companion-rec-question">Confidence</div>
          <div className="lw-companion-rec-evidence">
            <span className="lw-companion-rec-conf">{confidenceLabel(top.confidence)}</span>
            {top.source_observation && (
              <span className="lw-companion-rec-source">— based on {top.source_observation}</span>
            )}
          </div>
        </div>
        <div className="lw-companion-rec-actions">
          <motion.button
            className="lw-companion-rec-btn lw-companion-rec-btn-primary"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onExecute(top)}
          >
            {top.action_label}
          </motion.button>
          <motion.button
            className="lw-companion-rec-btn lw-companion-rec-btn-alt"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onDismiss(top.id)}
          >
            Not now
          </motion.button>
        </div>
      </motion.div>

      {/* Alternatives */}
      {others.length > 0 && (
        <div className="lw-companion-alts">
          <p className="lw-companion-alts-label">Alternatives to consider:</p>
          {others.slice(0, 2).map((rec) => (
            <div key={rec.id} className="lw-companion-alt-item">
              <span className="lw-companion-alt-title">{rec.title}</span>
              <button
                className="lw-companion-alt-exec"
                onClick={() => onExecute(rec)}
              >
                {rec.action_label}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Companion Header ───────────────────────────────────────────────

const CompanionHeader: FC<{
  isWorking: boolean;
  observationCount: number;
  executionCount: number;
}> = ({ isWorking, observationCount, executionCount }) => {
  return (
    <div className="lw-companion-header">
      <motion.div
        className="lw-companion-avatar"
        animate={{
          boxShadow: isWorking
            ? ['0 0 4px var(--lw-teal)', '0 0 12px var(--lw-teal)', '0 0 4px var(--lw-teal)']
            : '0 0 4px var(--lw-green)',
        }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <span
          className="lw-companion-dot"
          style={{
            backgroundColor: isWorking ? 'var(--lw-teal)' : 'var(--lw-green)',
          }}
        />
      </motion.div>
      <div className="lw-companion-id">
        <span className="lw-companion-name">SHUNYA</span>
        <span className="lw-companion-state">
          {isWorking
            ? `Working on ${executionCount} task${executionCount !== 1 ? 's' : ''}`
            : observationCount > 0
            ? `${observationCount} observation${observationCount !== 1 ? 's' : ''} to share`
            : 'Observing'}
        </span>
      </div>
    </div>
  );
};

// ── Main Component ─────────────────────────────────────────────────

export const AIPresencePanel: FC = () => {
  const [showMemoryReview, setShowMemoryReview] = useState(false);
  const {
    observations,
    recommendations,
    activeExecutions,
    executionHistory,
    realityEvents,
    executeAction,
    dismissRecommendation,
    fetchLivingObjects,
    fetchReality,
    reflectionMessages,
    getAdaptationContext,
    dismissReflection,
    founderPreferences,
  } = useLivingStore();

  const handleExecute = (rec: AIRecommendation) => {
    const payload = {
      ...rec.action_payload,
      label: rec.action_label,
    };
    executeAction(rec.action_type, payload).then(() => {
      fetchLivingObjects();
      fetchReality();
    });
  };

  const isWorking = activeExecutions.length > 0;

  return (
    <div className="lw-companion">
      <CompanionHeader
        isWorking={isWorking}
        observationCount={observations.length}
        executionCount={activeExecutions.length}
      />

      {/* 0. Adaptation Context — before any other content */}
      {getAdaptationContext() && (
        <div className="lw-companion-section">
          <p className="lw-companion-narrative lw-companion-quiet">
            {getAdaptationContext()}
          </p>
        </div>
      )}

      {/* 0b. Reflection Messages */}
      {reflectionMessages.filter((r) => !r.seen).slice(0, 1).map((ref) => (
        <div key={ref.id} className="lw-companion-reflection">
          <p className="lw-companion-reflection-text">{ref.message}</p>
          <button
            className="lw-companion-reflection-dismiss"
            onClick={() => dismissReflection(ref.id)}
          >
            Got it
          </button>
        </div>
      ))}

      {/* 1. What has SHUNYA already done? */}
      <WhatHasBeenDone
        observations={observations}
        executionHistory={executionHistory}
        realityEventCount={realityEvents.length}
      />

      {/* 2. What is SHUNYA doing now? */}
      <WhatIsHappeningNow executions={activeExecutions} />

      {/* 2b. Continuous Ownership — what SHUNYA will monitor after execution */}
      {executionHistory.length > 0 && activeExecutions.length === 0 && (
        <div className="lw-companion-section">
          <p className="lw-companion-narrative lw-companion-quiet">
            I've completed what you asked. I'll keep watching for any changes
            and let you know if something needs your attention.
          </p>
        </div>
      )}

      {/* 3. What is SHUNYA waiting for? */}
      <WhatIsBeingMonitored observations={observations} />

      {/* 4. What does SHUNYA recommend next? */}
      <WhatHappensNext
        recommendations={recommendations}
        onExecute={handleExecute}
        onDismiss={dismissRecommendation}
      />

      {/* 5. Memory Governance — explainable, reviewable, resettable */}
      {founderPreferences.totalInteractions >= 3 && (
        <div className="lw-companion-section">
          <button
            className="lw-companion-memory-link"
            onClick={() => setShowMemoryReview(!showMemoryReview)}
          >
            {showMemoryReview ? 'Hide' : 'Review'} what SHUNYA knows about you
          </button>
        </div>
      )}

      {showMemoryReview && <MemoryReview />}
    </div>
  );
};