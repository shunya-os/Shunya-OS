/**
 * SHUNYA LX-05 — Memory Review
 *
 * The founder must always understand:
 *   what SHUNYA learned,
 *   why it learned it,
 *   where it is stored,
 *   how to modify it,
 *   how to remove it.
 *
 * This panel is accessible from the Companion.
 * No hidden behavioural model exists.
 */

import { useState, type FC } from 'react';
import { motion } from 'framer-motion';
import { useLivingStore } from './living-store';

export const MemoryReview: FC = () => {
  const {
    founderPreferences,
    interactionHistory,
    reflectionMessages,
    resetFounderMemory,
  } = useLivingStore();
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const executedCount = interactionHistory.filter((h) => h.outcome === 'executed').length;
  const dismissedCount = interactionHistory.filter((h) => h.outcome === 'dismissed').length;

  return (
    <div className="lw-memory-review">
      <div className="lw-memory-header">
        <h3 className="lw-memory-title">What SHUNYA Knows About You</h3>
        <p className="lw-memory-sub">
          This information stays on this device and is never shared.
          You can review, understand, or reset it at any time.
        </p>
      </div>

      {/* Memory Classification */}
      <div className="lw-memory-classification">
        <div className="lw-memory-tier">
          <span className="lw-memory-tier-tag lw-tier-session">Session</span>
          <span className="lw-memory-tier-desc">Discarded when you close SHUNYA</span>
        </div>
        <div className="lw-memory-tier">
          <span className="lw-memory-tier-tag lw-tier-founder">Founder</span>
          <span className="lw-memory-tier-desc">Explainable, reviewable, resettable</span>
        </div>
        <div className="lw-memory-tier">
          <span className="lw-memory-tier-tag lw-tier-business">Business</span>
          <span className="lw-memory-tier-desc">Permanent canonical truth (objects, outcomes)</span>
        </div>
      </div>

      {/* Founder Preferences */}
      <div className="lw-memory-section">
        <div className="lw-memory-section-title">
          Adaptation Level
          <span className="lw-memory-badge">{Math.round(founderPreferences.confidence * 100)}%</span>
        </div>
        <p className="lw-memory-section-desc">
          Based on {founderPreferences.totalInteractions} interaction{founderPreferences.totalInteractions !== 1 ? 's' : ''}
          ({executedCount} executed, {dismissedCount} dismissed)
        </p>

        {founderPreferences.activeObjectTypes.length > 0 && (
          <div className="lw-memory-row">
            <span className="lw-memory-label">Engaged object types:</span>
            <span className="lw-memory-value">{founderPreferences.activeObjectTypes.join(', ')}</span>
          </div>
        )}

        {Object.entries(founderPreferences.preferredActions).length > 0 && (
          <div className="lw-memory-row">
            <span className="lw-memory-label">Preferred actions:</span>
            <div className="lw-memory-action-list">
              {Object.entries(founderPreferences.preferredActions).map(([type, actions]) => (
                <div key={type} className="lw-memory-action-item">
                  <span className="lw-memory-action-type">{type}</span>
                  <span className="lw-memory-action-names">{actions.slice(0, 3).join(', ')}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="lw-memory-row">
          <span className="lw-memory-label">Prepared action approval:</span>
          <span className="lw-memory-value">
            {founderPreferences.approvesPreparedActions ? 'Tends to approve' : 'Still learning'}
          </span>
        </div>
      </div>

      {/* Reflection History */}
      {reflectionMessages.length > 0 && (
        <div className="lw-memory-section">
          <div className="lw-memory-section-title">
            What SHUNYA Has Communicated
            <span className="lw-memory-badge">{reflectionMessages.length}</span>
          </div>
          <div className="lw-memory-reflections">
            {reflectionMessages.map((ref) => (
              <div key={ref.id} className="lw-memory-reflection-item">
                <p className="lw-memory-reflection-text">{ref.message}</p>
                <span className="lw-memory-reflection-type">{ref.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Storage Location */}
      <div className="lw-memory-section">
        <div className="lw-memory-section-title">Storage Location</div>
        <p className="lw-memory-section-desc">
          All adaptation data is stored in browser session memory — it is discarded when you close SHUNYA.
          Until Launch Candidate, no founder behaviour is persisted to the server.
        </p>
      </div>

      {/* Reset */}
      <div className="lw-memory-section">
        <div className="lw-memory-section-title">Reset Adaptation</div>
        <p className="lw-memory-section-desc">
          This clears all preferences and interaction history SHUNYA has learned about you.
          Recommendations will return to their default behaviour until SHUNYA observes new patterns.
        </p>
        {!showResetConfirm ? (
          <motion.button
            className="lw-memory-reset-btn"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowResetConfirm(true)}
          >
            Reset what SHUNYA knows about me
          </motion.button>
        ) : (
          <motion.div
            className="lw-memory-reset-confirm"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <p className="lw-memory-reset-warn">Are you sure? This cannot be undone within this session.</p>
            <div className="lw-memory-reset-actions">
              <button
                className="lw-memory-reset-yes"
                onClick={() => { resetFounderMemory(); setShowResetConfirm(false); }}
              >
                Yes, reset
              </button>
              <button
                className="lw-memory-reset-no"
                onClick={() => setShowResetConfirm(false)}
              >
                Cancel
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};