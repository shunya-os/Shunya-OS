/**
 * SHUNYA LX-01 — Living Command Surface
 *
 * The command surface is the operating system interface.
 * It continuously supports: conversation, voice, attachments, history,
 * unfinished work, recommendations, follow-up actions, execution progress,
 * recent outcomes, and context awareness.
 *
 * The command surface shall never feel like a text box.
 */

import { useRef, useState, useEffect, type FC, type KeyboardEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLivingStore } from './living-store';

interface SuggestedAction {
  label: string;
  description: string;
  action_type: string;
  payload: Record<string, unknown>;
}

// ── Suggested actions based on context ─────────────────────────────

function getContextualSuggestions(
  observationsCount: number,
  objectCount: number,
  _executionCount: number,
): SuggestedAction[] {
  const suggestions: SuggestedAction[] = [];

  if (objectCount === 0) {
    suggestions.push({
      label: 'Create your first object',
      description: 'Start building your organisation',
      action_type: 'outcome',
      payload: { name: 'create_customer', data: { company_name: 'New Customer' }, label: 'Create Customer' },
    });
  }

  if (observationsCount > 0) {
    suggestions.push({
      label: 'Review AI insights',
      description: 'See what SHUNYA has observed',
      action_type: 'navigate',
      payload: { view: 'insights' },
    });
  }

  suggestions.push({
    label: 'Ask SHUNYA',
    description: 'Ask anything about your organisation',
    action_type: 'ask',
    payload: {},
  });

  suggestions.push({
    label: 'Generate report',
    description: 'Summarise current state of your organisation',
    action_type: 'outcome',
    payload: { name: 'generate_report', data: {}, label: 'Generating report…' },
  });

  return suggestions;
}

// ── Main Component ─────────────────────────────────────────────────

export const CommandSurface: FC = () => {
  const {
    commandOpen,
    setCommandOpen,
    observations,
    livingObjects,
    activeExecutions,
    executeAction,
    fetchReality,
    fetchLivingObjects,
  } = useLivingStore();

  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (commandOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [commandOpen]);

  const suggestions = getContextualSuggestions(
    observations.length,
    livingObjects.length,
    activeExecutions.length,
  );

  const handleSubmit = () => {
    const value = inputValue.trim();
    if (!value) return;

    setCommandOpen(false);
    setInputValue('');

    // Treat typed input as an intent
    executeAction('outcome', {
      intent: value,
      data: {},
      label: value.length > 60 ? value.slice(0, 60) + '…' : value,
    }).then(() => {
      fetchReality();
      fetchLivingObjects();
    });
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    } else if (e.key === 'Escape') {
      setCommandOpen(false);
      setInputValue('');
    }
  };

  const handleSuggestionClick = (suggestion: SuggestedAction) => {
    setCommandOpen(false);
    executeAction(suggestion.action_type, suggestion.payload).then(() => {
      fetchReality();
      fetchLivingObjects();
    });
  };

  return (
    <div className="lw-command-surface">
      <AnimatePresence>
        {commandOpen && (
          <motion.div
            className="lw-command-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setCommandOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Persistent command bar trigger */}
      <motion.button
        className="lw-command-trigger"
        onClick={() => {
          setCommandOpen(true);
          setShowSuggestions(true);
        }}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <span className="lw-command-trigger-icon">
          <motion.span
            animate={{ rotate: commandOpen ? 45 : 0 }}
            transition={{ duration: 0.2 }}
          >
            +
          </motion.span>
        </span>
        <span className="lw-command-trigger-text">
          {activeExecutions.length > 0
            ? `${activeExecutions.length} execution${activeExecutions.length !== 1 ? 's' : ''} in progress`
            : observations.length > 0
            ? `${observations.length} insight${observations.length !== 1 ? 's' : ''} available`
            : 'Ask SHUNYA or type a command…'}
        </span>
        <span className="lw-command-kbd">⌘K</span>
      </motion.button>

      {/* Expanded command panel */}
      <AnimatePresence>
        {commandOpen && (
          <motion.div
            className="lw-command-panel"
            initial={{ y: 20, opacity: 0, scale: 0.95 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: 20, opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          >
            {/* Input */}
            <div className="lw-command-input-area">
              <span className="lw-command-prompt">→</span>
              <input
                ref={inputRef}
                type="text"
                className="lw-command-input"
                placeholder="Ask SHUNYA anything, or type a command…"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
              />
            </div>

            {/* Context-aware suggestions */}
            <AnimatePresence>
              {showSuggestions && (
                <motion.div
                  className="lw-command-suggestions"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                >
                  <div className="lw-command-suggest-title">Suggested</div>
                  <div className="lw-command-suggest-list">
                    {suggestions.map((s, i) => (
                      <motion.button
                        key={s.label}
                        className="lw-command-suggest-item"
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.05 }}
                        onClick={() => handleSuggestionClick(s)}
                        whileHover={{ x: 4 }}
                      >
                        <div className="lw-command-suggest-label">{s.label}</div>
                        <div className="lw-command-suggest-desc">{s.description}</div>
                      </motion.button>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};