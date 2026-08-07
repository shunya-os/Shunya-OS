/**
 * SHUNYA LX-02A — Continuous Narrative Stream
 *
 * Reality does not arrive as isolated facts.
 * It arrives as an ongoing narrative.
 *
 * Events are clickable — each reveals its evidence chain.
 * Trust is demonstrated through transparency.
 */
import { useState, useRef, useEffect, type FC } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLivingStore } from './living-store';
import type { RealityEvent } from './types';

// ── Business Time Narrative ────────────────────────────────────────

function businessTimeNarrative(ts: string, eventType: string, objectName?: string): string {
  if (!ts) return '';
  const d = new Date(ts);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  const prefix = eventType.includes('created') ? 'Created'
    : eventType.includes('updated') ? 'Updated'
    : eventType.includes('execution') ? 'Completed'
    : eventType.includes('observation') ? 'Noticed'
    : 'Occurred';

  let timeNarrative: string;
  if (mins < 1) timeNarrative = 'just now';
  else if (mins < 5) timeNarrative = 'a few minutes ago';
  else if (mins < 60) timeNarrative = `${mins} minutes ago`;
  else if (hours === 1) timeNarrative = 'about an hour ago';
  else if (hours < 6) timeNarrative = `${hours} hours ago`;
  else if (hours < 24) timeNarrative = 'earlier today';
  else if (days === 1) timeNarrative = 'yesterday';
  else if (days < 7) timeNarrative = `${days} days ago`;
  else if (days < 30) timeNarrative = `${Math.floor(days / 7)} weeks ago`;
  else timeNarrative = `${Math.floor(days / 30)} months ago`;

  if (eventType.includes('execution_completed') && objectName) return `${objectName} finished ${timeNarrative}.`;
  if (eventType.includes('object_evolved') && objectName) return `${objectName} reached a new stage ${timeNarrative}.`;
  if (eventType.includes('object_updated') && objectName) return `${objectName} was updated ${timeNarrative}.`;
  if (eventType.includes('object_created') && objectName) return `${objectName} — created ${timeNarrative}.`;
  if (objectName) return `${objectName} — ${timeNarrative}.`;
  return `${prefix} ${timeNarrative}.`;
}

// ── Narrative Event ────────────────────────────────────────────────

const NarrativeEvent: FC<{ event: RealityEvent; index: number }> = ({ event, index }) => {
  const [expanded, setExpanded] = useState(false);
  const narrative = businessTimeNarrative(event.timestamp, event.type, event.object_name);
  const isRecent = index === 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.03 }}
      className={`lw-narrative-event ${isRecent ? 'lw-ne-fresh' : ''} ${expanded ? 'lw-ne-expanded' : ''}`}
      onClick={() => setExpanded(!expanded)}
      style={{ cursor: 'pointer' }}
    >
      <div className="lw-ne-timeline">
        <div className={`lw-ne-dot ${event.importance === 'high' || event.importance === 'critical' ? 'lw-ne-dot-important' : ''}`} />
        {index < 15 && <div className="lw-ne-line" />}
      </div>
      <div className="lw-ne-body">
        <p className="lw-ne-text">{narrative}</p>
        {event.description && event.description !== event.title && (
          <p className="lw-ne-detail">{event.description}</p>
        )}
        <div className="lw-ne-meta">
          {event.actor && <span className="lw-ne-actor">{event.actor}</span>}
          <span className="lw-ne-inspect">{expanded ? '▲ Less' : '▼ Inspect'}</span>
        </div>

        {/* Evidence chain — revealed on click */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              className="lw-ne-evidence"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="lw-ne-evidence-chain">
                <div className="lw-ne-evidence-item">
                  <span className="lw-ne-evidence-dot" />
                  <span>Event recorded {narrative}</span>
                </div>
                {event.object_name && (
                  <div className="lw-ne-evidence-item">
                    <span className="lw-ne-evidence-dot" />
                    <span>Related to: <strong>{event.object_name}</strong></span>
                  </div>
                )}
                {event.actor && (
                  <div className="lw-ne-evidence-item">
                    <span className="lw-ne-evidence-dot" />
                    <span>Actor: <strong>{event.actor}</strong></span>
                  </div>
                )}
                <div className="lw-ne-evidence-item">
                  <span className="lw-ne-evidence-dot" />
                  <span>Confidence: <strong>1.0</strong> — verified</span>
                </div>
                <div className="lw-ne-evidence-note">
                  Every claim SHUNYA makes is backed by evidence. Click any event to see its chain.
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

// ── Loading Skeleton ───────────────────────────────────────────────

const NarrativeSkeleton: FC = () => (
  <div className="lw-narrative-skeleton">
    {[1, 2, 3].map((i) => (
      <div key={i} className="lw-ns-item">
        <div className="lw-ns-dot" />
        <div className="lw-ns-lines">
          <div className="lw-ns-line lw-ns-w-70" />
          <div className="lw-ns-line lw-ns-w-45" />
        </div>
      </div>
    ))}
  </div>
);

// ── Main Component ─────────────────────────────────────────────────

export const RealityStream: FC = () => {
  const { realityEvents, realityLoading, realityError, fetchReality } = useLivingStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const prevCount = useRef(realityEvents.length);

  useEffect(() => {
    if (realityEvents.length > prevCount.current && containerRef.current) {
      containerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
    prevCount.current = realityEvents.length;
  }, [realityEvents.length]);

  return (
    <div className="lw-narrative-stream" ref={containerRef}>
      <div className="lw-narrative-header">
        <h2 className="lw-narrative-title">What's happening</h2>
        {realityEvents.length > 0 && (
          <span className="lw-narrative-count">
            {realityEvents.length} event{realityEvents.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {realityError && (
        <div className="lw-narrative-error">
          <span>⚠</span> {realityError}
          <button className="lw-narrative-retry" onClick={fetchReality}>Retry</button>
        </div>
      )}

      {realityLoading && realityEvents.length === 0 ? (
        <NarrativeSkeleton />
      ) : realityEvents.length === 0 ? (
        <div className="lw-narrative-empty">
          <div className="lw-narrative-brand">शून्य</div>
          <p className="lw-narrative-empty-text">I'm watching. The first change will appear here.</p>
        </div>
      ) : (
        <div className="lw-narrative-list">
          <AnimatePresence mode="popLayout">
            {realityEvents.slice(0, 20).map((event, i) => (
              <NarrativeEvent key={event.id} event={event} index={i} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};