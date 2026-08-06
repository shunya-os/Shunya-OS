/**
 * SHUNYA LX-02A — Executive Briefing (Companion Greeting)
 *
 * The first thing the founder sees — not a dashboard, not a menu.
 * A companion greeting that references previous work, explains
 * what SHUNYA has been doing, and sets the tone for the session.
 *
 * "Good afternoon. While you were away, I completed two tasks
 *  and noticed three changes worth reviewing."
 */

import { useState, useEffect, type FC } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLivingStore } from './living-store';
import type { AIRecommendation, Execution } from './types';

// ── Journey Stage Tracking ─────────────────────────────────────────

type JourneyStage = 'briefing' | 'recommendation' | 'execution' | 'outcome' | 'followup';

interface JourneyState {
  completedStages: JourneyStage[];
  currentStage: JourneyStage;
  startedAt: string;
  followUpActions: string[];
}

// ── Helpers ────────────────────────────────────────────────────────

function formatBriefingTime(): string {
  const now = new Date();
  const hour = now.getHours();
  const period = hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening';
  return period;
}

// ── Briefing Header ────────────────────────────────────────────────

const BriefingHeader: FC<{
  founderName: string;
  priorityCount: number;
  observationCount: number;
  executionCount: number;
}> = ({ founderName, priorityCount, observationCount, executionCount }) => {
  const timeOfDay = formatBriefingTime();

  // Build a companion narrative for the greeting
  let companionMessage: string;
  if (executionCount > 0) {
    companionMessage = `While you were away, I've been working on ${executionCount} task${executionCount !== 1 ? 's' : ''}. ${observationCount > 0 ? `${observationCount} thing${observationCount !== 1 ? 's' : ''} caught my attention that I'd like to discuss.` : ''}`;
  } else if (observationCount > 1) {
    companionMessage = `I noticed ${observationCount} change${observationCount !== 1 ? 's' : ''} since your last visit. ${priorityCount > 0 ? `${priorityCount} of them need${priorityCount === 1 ? 's' : ''} your attention.` : 'Nothing urgent, but worth reviewing.'}`;
  } else if (observationCount === 1) {
    companionMessage = `One thing I've been monitoring — I think it's worth a quick look.`;
  } else {
    companionMessage = `Everything looks steady. I'm keeping watch — I'll let you know when something changes.`;
  }

  return (
    <motion.div
      className="lw-briefing-header"
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="lw-briefing-time">
        Good {timeOfDay}, {founderName}
      </div>
      <p className="lw-briefing-companion">{companionMessage}</p>
    </motion.div>
  );
};

// ── Briefing Priority Overview ─────────────────────────────────────

const PriorityOverview: FC<{
  priorities: AIRecommendation[];
  onExecute: (rec: AIRecommendation) => void;
}> = ({ priorities, onExecute }) => {
  if (priorities.length === 0) return null;

  const topPriority = priorities[0];
  const otherPriorities = priorities.slice(1);

  return (
    <div className="lw-briefing-section">
      <div className="lw-briefing-section-header">
        <span className="lw-briefing-section-icon">⬡</span>
        <span className="lw-briefing-section-title">
          {priorities.length} Priorit{priorities.length === 1 ? 'y' : 'ies'}
        </span>
      </div>

      {/* Top priority — prominent */}
      <motion.div
        className="lw-briefing-top-priority"
        layoutId={`priority-${topPriority.id}`}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        <div className="lw-bp-header">
          <span className="lw-bp-urgency">
            {topPriority.urgency === 'now' ? '⬡ Now' : topPriority.urgency === 'today' ? '◈ Today' : '◇ This Week'}
          </span>
          <span className="lw-bp-confidence">
            {Math.round(topPriority.confidence * 100)}% confidence
          </span>
        </div>
        <h3 className="lw-bp-title">{topPriority.title}</h3>
        <p className="lw-bp-desc">{topPriority.description}</p>
        <motion.button
          className="lw-bp-execute"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onExecute(topPriority)}
        >
          → {topPriority.action_label}
        </motion.button>
      </motion.div>

      {/* Other priorities — compact */}
      {otherPriorities.length > 0 && (
        <div className="lw-briefing-other-priorities">
          {otherPriorities.slice(0, 3).map((p) => (
            <motion.div
              key={p.id}
              className="lw-briefing-other-p"
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              whileHover={{ backgroundColor: 'var(--lw-surface-raised)' }}
            >
              <div className="lw-bop-left">
                <span className="lw-bop-urgency-icon">
                  {p.urgency === 'now' ? '⬡' : p.urgency === 'today' ? '◈' : '◇'}
                </span>
                <span className="lw-bop-title">{p.title}</span>
              </div>
              <button
                className="lw-bop-execute"
                onClick={() => onExecute(p)}
              >
                {p.action_label}
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Helper Functions (unused RecommendationCard removed) ──


// ── Execution Progress ─────────────────────────────────────────────

const ExecutionProgressView: FC<{ executions: Execution[] }> = ({ executions }) => {
  return (
    <motion.div
      className="lw-briefing-section"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="lw-briefing-section-header">
        <motion.span
          className="lw-briefing-section-icon"
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        >
          ⟳
        </motion.span>
        <span className="lw-briefing-section-title">
          Executing {executions.length} action{executions.length !== 1 ? 's' : ''}
        </span>
      </div>
      <div className="lw-briefing-exec-list">
        {executions.map((exec) => (
          <motion.div
            key={exec.id}
            className="lw-briefing-exec-item"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
          >
            <div className="lw-briefing-exec-label">{exec.label}</div>
            <div className="lw-briefing-exec-track">
              <motion.div
                className="lw-briefing-exec-fill"
                initial={{ width: 0 }}
                animate={{ width: `${Math.round(exec.progress * 100)}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
            <div className="lw-briefing-exec-pct">
              {Math.round(exec.progress * 100)}%
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

// ── Outcome Display ────────────────────────────────────────────────

const OutcomeDisplay: FC<{ execution: Execution }> = ({ execution }) => {
  const isSuccess = execution.status === 'completed';
  return (
    <motion.div
      className={`lw-briefing-outcome ${isSuccess ? 'lw-bo-success' : 'lw-bo-fail'}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="lw-bo-icon">{isSuccess ? '✓' : '✕'}</div>
      <div className="lw-bo-body">
        <div className="lw-bo-title">{execution.label}</div>
        {execution.outcome && (
          <p className="lw-bo-desc">{execution.outcome}</p>
        )}
        {execution.error && (
          <p className="lw-bo-error">{execution.error}</p>
        )}
      </div>
    </motion.div>
  );
};

// ── Follow-up Suggestions ──────────────────────────────────────────

const FollowUpSuggestions: FC<{ onExecute: (action: string) => void }> = ({ onExecute }) => {
  const suggestions = [
    { label: 'Review updated state', action: 'View reality stream' },
    { label: 'Start next briefing cycle', action: 'Refresh briefing' },
    { label: 'Explore new insights', action: 'Open AI insights' },
    { label: 'Create a follow-up object', action: 'Create follow-up' },
  ];

  return (
    <motion.div
      className="lw-briefing-section"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
    >
      <div className="lw-briefing-section-header">
        <span className="lw-briefing-section-icon">→</span>
        <span className="lw-briefing-section-title">Follow-up</span>
      </div>
      <div className="lw-briefing-followups">
        {suggestions.map((s, i) => (
          <motion.button
            key={s.label}
            className="lw-briefing-followup"
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 + i * 0.1 }}
            whileHover={{ x: 4 }}
            onClick={() => onExecute(s.label)}
          >
            <span className="lw-bf-icon">→</span>
            <span className="lw-bf-label">{s.label}</span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
};

// ── Main Executive Briefing Component ──────────────────────────────

export const ExecutiveBriefing: FC = () => {
  const {
    founderName,
    recommendations,
    observations,
    activeExecutions,
    executionHistory,
    executeAction,
    fetchReality,
    fetchLivingObjects,
  } = useLivingStore();

  const [journey, setJourney] = useState<JourneyState>({
    completedStages: [],
    currentStage: 'briefing',
    startedAt: new Date().toISOString(),
    followUpActions: [],
  });

  // Track journey progression based on state
  useEffect(() => {
    const completed = [...journey.completedStages];

    // Briefing → Recommendation (automatic after data loads)
    if (journey.currentStage === 'briefing' && (recommendations.length > 0 || observations.length > 0)) {
      if (!completed.includes('briefing')) {
        completed.push('briefing');
      }
      setJourney((prev) => ({
        ...prev,
        completedStages: completed,
        currentStage: 'recommendation',
      }));
    }

    // Recommendation → Execution (when user executes)
    if (activeExecutions.length > 0 && journey.currentStage === 'recommendation') {
      if (!completed.includes('recommendation')) {
        completed.push('recommendation');
      }
      setJourney((prev) => ({
        ...prev,
        completedStages: completed,
        currentStage: 'execution',
      }));
    }

    // Execution → Outcome (when executions complete and history has items)
    if (activeExecutions.length === 0 && executionHistory.length > 0 && journey.currentStage === 'execution') {
      if (!completed.includes('execution')) {
        completed.push('execution');
      }
      setJourney((prev) => ({
        ...prev,
        completedStages: completed,
        currentStage: 'outcome',
      }));
    }

    // Outcome → Follow-up (automatic)
    if (journey.currentStage === 'outcome' && executionHistory.length > 0) {
      if (!completed.includes('outcome')) {
        completed.push('outcome');
      }
      setJourney((prev) => ({
        ...prev,
        completedStages: completed,
        currentStage: 'followup',
      }));
    }
  }, [recommendations, observations, activeExecutions, executionHistory, journey]);

  const handleExecute = (rec: AIRecommendation) => {
    executeAction(rec.action_type, {
      ...rec.action_payload,
      label: rec.action_label,
    }).then(() => {
      fetchReality();
      fetchLivingObjects();
    });
  };

  const handleFollowUpAction = (action: string) => {
    setJourney((prev) => ({
      ...prev,
      followUpActions: [...prev.followUpActions, action],
    }));
  };

  const recentOutcomes = executionHistory.slice(-2);

  return (
    <div className="lw-briefing">
      {/* Journey Stage Indicator */}
      <div className="lw-briefing-stages">
        {(['briefing', 'recommendation', 'execution', 'outcome', 'followup'] as JourneyStage[]).map((stage, i) => {
          const isComplete = journey.completedStages.includes(stage);
          const isCurrent = stage === journey.currentStage;
          const labels: Record<JourneyStage, string> = {
            briefing: 'Briefing', recommendation: 'Recommend',
            execution: 'Execute', outcome: 'Outcome', followup: 'Follow-up',
          };
          return (
            <div
              key={stage}
              className={`lw-bs-stage ${isComplete ? 'lw-bs-done' : ''} ${isCurrent ? 'lw-bs-current' : ''}`}
            >
              <div className="lw-bs-dot">
                {isComplete ? '✓' : isCurrent ? '○' : '·'}
              </div>
              <span className="lw-bs-label">{labels[stage]}</span>
              {i < 4 && <div className={`lw-bs-line ${isComplete ? 'lw-bs-line-done' : ''}`} />}
            </div>
          );
        })}
      </div>

      {/* Briefing Content */}
      <BriefingHeader
        founderName={founderName}
        priorityCount={recommendations.length}
        observationCount={observations.length}
        executionCount={activeExecutions.length}
      />

      {journey.currentStage === 'briefing' && (
        <motion.p
          className="lw-briefing-loading"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          SHUNYA is gathering your briefing…
        </motion.p>
      )}

      {/* Priorities — visible in briefing and recommendation stages */}
      {(journey.currentStage === 'briefing' || journey.currentStage === 'recommendation') && (
        <PriorityOverview priorities={recommendations} onExecute={handleExecute} />
      )}

      {/* Active Executions */}
      {activeExecutions.length > 0 && (
        <ExecutionProgressView executions={activeExecutions} />
      )}

      {/* Recent Outcomes */}
      {journey.currentStage === 'outcome' && recentOutcomes.length > 0 && (
        <div className="lw-briefing-section">
          <div className="lw-briefing-section-header">
            <span className="lw-briefing-section-icon">✓</span>
            <span className="lw-briefing-section-title">Outcome{recentOutcomes.length > 1 ? 's' : ''}</span>
          </div>
          <div className="lw-briefing-outcomes">
            <AnimatePresence>
              {recentOutcomes.map((exec) => (
                <OutcomeDisplay key={exec.id} execution={exec} />
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Follow-up */}
      {journey.currentStage === 'followup' && (
        <FollowUpSuggestions onExecute={handleFollowUpAction} />
      )}
    </div>
  );
};