/**
 * SHUNYA LX-02 — Living Object Card
 *
 * Every business object as a continuously evolving story.
 *
 * When expanded, reveals in 10 seconds:
 * - Where it came from (stage history)
 * - What has happened (time narrative + stages)
 * - Why it matters (relationship stories)
 * - What SHUNYA is monitoring (observations)
 * - What should happen next (recommendation with reasoning)
 *
 * Object expansion feels like reality unfolding — not opening another page.
 */

import { type FC } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLivingStore } from './living-store';
import type { LivingObject } from './types';

// ── Helpers ────────────────────────────────────────────────────────

function formatTimeAgo(ts: string): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

function confidenceColor(c: number): string {
  if (c >= 0.85) return 'var(--lw-green)';
  if (c >= 0.7) return 'var(--lw-teal)';
  if (c >= 0.5) return 'var(--lw-amber)';
  return 'var(--lw-gray)';
}

// ── Stage Pipeline ─────────────────────────────────────────────────

const StagePipeline: FC<{ pipeline: string[]; current: string }> = ({ pipeline, current }) => {
  const currentIdx = pipeline.indexOf(current);
  if (currentIdx === -1) return null;

  const visible = pipeline.slice(Math.max(0, currentIdx - 2), currentIdx + 3);

  return (
    <div className="lw-obj-pipeline">
      {visible.map((stage, i) => {
        const idx = pipeline.indexOf(stage);
        const isCompleted = idx < currentIdx;
        const isCurrent = stage === current;
        const isFuture = idx > currentIdx;

        return (
          <div
            key={stage}
            className={`lw-ps-stage ${isCompleted ? 'lw-ps-completed' : ''} ${isCurrent ? 'lw-ps-current' : ''} ${isFuture ? 'lw-ps-future' : ''}`}
          >
            <div className="lw-ps-dot-wrap">
              <motion.div
                className="lw-ps-dot"
                animate={isCurrent ? {
                  scale: [1, 1.4, 1],
                  boxShadow: ['0 0 0 0 rgba(212, 168, 75, 0.4)', '0 0 0 6px rgba(212, 168, 75, 0.15)', '0 0 0 0 rgba(212, 168, 75, 0.4)'],
                } : {}}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </div>
            <span className="lw-ps-label">{stage}</span>
            {i < visible.length - 1 && (
              <div className={`lw-ps-connector ${isCompleted ? 'lw-ps-connector-done' : ''}`} />
            )}
          </div>
        );
      })}
    </div>
  );
};

// ── Time Narrative ─────────────────────────────────────────────────

const TimeNarrative: FC<{ text: string; stages: LivingObject['stage_history'] }> = ({ text, stages }) => {
  return (
    <div className="lw-obj-section lw-obj-section-compact">
      <div className="lw-obj-section-title">Timeline</div>
      <p className="lw-obj-time-narrative">{text}</p>
      {stages.length > 0 && (
        <div className="lw-obj-stage-list">
          {stages.slice(0, 4).map((s, i) => (
            <div key={i} className="lw-obj-stage-item">
              <div className="lw-obj-stage-dot" />
              <span className="lw-obj-stage-label">{s.label}</span>
              {s.timestamp && <span className="lw-obj-stage-time">{formatTimeAgo(s.timestamp)}</span>}
              {s.actor && <span className="lw-obj-stage-actor">by {s.actor}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Relationship Story ─────────────────────────────────────────────

const RelationshipStories: FC<{ relationships: LivingObject['relationships'] }> = ({ relationships }) => {
  if (relationships.length === 0) return null;

  return (
    <div className="lw-obj-section">
      <div className="lw-obj-section-title">Connections</div>
      <div className="lw-obj-rel-flow">
        {relationships.map((rel, i) => (
          <motion.div
            key={i}
            className="lw-obj-rel-card"
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08 }}
          >
            <div className="lw-obj-rel-arrow">
              {rel.direction === 'outbound' ? '→' : '←'}
            </div>
            <div className="lw-obj-rel-body">
              <div className="lw-obj-rel-name">{rel.object_name}</div>
              <div className="lw-obj-rel-exp">{rel.explanation}</div>
              <div className="lw-obj-rel-conf">
                <span
                  className="lw-obj-rel-conf-dot"
                  style={{ backgroundColor: confidenceColor(rel.confidence) }}
                />
                {Math.round(rel.confidence * 100)}% confidence
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// ── Recommendation ─────────────────────────────────────────────────

const RecommendationBlock: FC<{
  rec: LivingObject['recommendation'];
  onExecute: (label: string, type: string) => void;
}> = ({ rec, onExecute }) => {
  if (!rec) return null;

  return (
    <div className="lw-obj-recommendation">
      <div className="lw-obj-rec-header">
        <span className="lw-obj-rec-icon">→</span>
        <span className="lw-obj-rec-label">Recommended: {rec.label}</span>
        <span
          className="lw-obj-rec-conf"
          style={{ color: confidenceColor(rec.confidence) }}
        >
          {Math.round(rec.confidence * 100)}%
        </span>
      </div>
      <p className="lw-obj-rec-reasoning">Because: {rec.reasoning}</p>
      <div className="lw-obj-rec-actions">
        <motion.button
          className="lw-obj-rec-execute"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onExecute(rec.label, rec.type)}
        >
          {rec.label}
        </motion.button>
        <motion.button
          className="lw-obj-rec-alt"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onExecute('Review alternatives', 'navigate')}
        >
          See alternatives
        </motion.button>
      </div>
    </div>
  );
};

// ── Main Card ──────────────────────────────────────────────────────

export const LivingObjectCard: FC<{ object: LivingObject; onOpenWorkspace?: (id: string, type: string, name: string) => void }> = ({ object, onOpenWorkspace }) => {
  const { expandedObjectId, expandObject, executeAction, fetchReality, fetchLivingObjects } = useLivingStore();
  const isExpanded = expandedObjectId === object.id;

  const handleAction = (label: string, actionType: string) => {
    executeAction(actionType, {
      name: `action_${object.object_type}`,
      data: { object_id: object.object_id },
      label,
    }).then(() => {
      fetchReality();
      fetchLivingObjects();
    });
  };

  const handleOpenDetail = () => {
    if (onOpenWorkspace) {
      onOpenWorkspace(object.object_id, object.object_type, object.name);
    } else {
      expandObject(isExpanded ? null : object.id);
    }
  };

  return (
    <motion.div
      layout
      className={`lw-living-object ${isExpanded ? 'lw-obj-expanded' : ''}`}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 200, damping: 25 }}
    >
      {/* Header — always visible: name, stage, summary, time */}
      <div
        className="lw-obj-header"
        onClick={handleOpenDetail}
        role="button"
        tabIndex={0}
      >
        <div className="lw-obj-title-row">
          <span className="lw-obj-icon">○</span>
          <span className="lw-obj-name">{object.name}</span>
          <span className="lw-obj-stage-badge">{object.current_stage}</span>
          {object.recommendation && object.recommendation.confidence >= 0.8 && !isExpanded && (
            <motion.button
              className="lw-obj-quick-action"
              onClick={(e) => { e.stopPropagation(); handleAction(object.recommendation.label, object.recommendation.type); }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              title={object.recommendation.reasoning}
            >
              {object.recommendation.label}
            </motion.button>
          )}
          <motion.span
            className="lw-obj-expand-icon"
            animate={{ rotate: isExpanded ? 90 : 0 }}
          >
            ›
          </motion.span>
        </div>
        <div className="lw-obj-meta-row">
          <span className="lw-obj-summary">{object.summary}</span>
          {object.time_narrative && (
            <span className="lw-obj-time-note">{object.time_narrative}</span>
          )}
        </div>
      </div>

      {/* Expanded content — reality unfolds */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease: 'easeInOut' }}
            className="lw-obj-body"
          >
            {/* 1. Stage Pipeline — where it is now in its journey */}
            {object.stage_pipeline.length > 0 && (
              <StagePipeline pipeline={object.stage_pipeline} current={object.current_stage} />
            )}

            {/* 2. Timeline — where it came from, what has happened */}
            <TimeNarrative text={object.time_narrative} stages={object.stage_history} />

            {/* 3. Relationship Stories — why it matters / what's connected */}
            <RelationshipStories relationships={object.relationships} />

            {/* 4. Recommendation — what should happen next (always last, always visible) */}
            <RecommendationBlock
              rec={object.recommendation}
              onExecute={handleAction}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};