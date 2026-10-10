/**
 * Keyboard Shortcuts — modal showing shortcuts by category.
 *
 * Opened by '?' keypress in executive-home.tsx, controlled via visible prop.
 */
import { useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { IconKeyboard, IconX } from '@tabler/icons-react';

interface Shortcut {
  keys: string[];
  label: string;
}

interface ShortcutCategory {
  id: string;
  label: string;
  items: Shortcut[];
}

const SHORTCUTS: ShortcutCategory[] = [
  {
    id: 'navigation',
    label: 'Navigation',
    items: [
      { keys: ['Ctrl', 'K'], label: 'Open command palette' },
      { keys: ['Ctrl', '1-9'], label: 'Switch to workspace tab' },
      { keys: ['Alt', 'Left'], label: 'Previous workspace' },
      { keys: ['Alt', 'Right'], label: 'Next workspace' },
      { keys: ['Esc'], label: 'Close current workspace / modal' },
    ],
  },
  {
    id: 'actions',
    label: 'Actions',
    items: [
      { keys: ['Ctrl', 'N'], label: 'Create new object' },
      { keys: ['Ctrl', 'S'], label: 'Save current workspace' },
      { keys: ['Ctrl', 'Z'], label: 'Undo' },
      { keys: ['Ctrl', 'Shift', 'Z'], label: 'Redo' },
      { keys: ['Ctrl', 'F'], label: 'Search in current view' },
    ],
  },
  {
    id: 'ai',
    label: 'AI',
    items: [
      { keys: ['Ctrl', 'Space'], label: 'Open AI assistant / Ask SHUNYA' },
      { keys: ['Ctrl', 'Enter'], label: 'Submit AI query' },
      { keys: ['Esc'], label: 'Close AI panel' },
    ],
  },
  {
    id: 'general',
    label: 'General',
    items: [
      { keys: ['?'], label: 'Show keyboard shortcuts (this modal)' },
      { keys: ['Ctrl', 'M'], label: 'Toggle sidebar' },
      { keys: ['Ctrl', 'L'], label: 'Focus command input' },
      { keys: ['Ctrl', 'Shift', 'E'], label: 'Export current view' },
      { keys: ['Ctrl', 'Shift', 'D'], label: 'Open developer tools' },
    ],
  },
];

function Kbd({ keys }: { keys: string[] }) {
  return (
    <span className="ks-kbd-group">
      {keys.map((k, i) => (
        <span key={i}>
          <kbd className="ks-kbd">{k}</kbd>
          {i < keys.length - 1 && <span className="ks-kbd-plus">+</span>}
        </span>
      ))}
    </span>
  );
}

export function KeyboardShortcuts({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape' && visible) {
      onClose();
    }
  }, [visible, onClose]);

  useEffect((): void | (() => void) => {
    if (visible) {
      window.addEventListener('keydown', handleKeyDown);
      return (): void => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [visible, handleKeyDown]);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="ks-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          onClick={onClose}
        >
          <motion.div
            className="ks-modal"
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="ks-header">
              <div className="ks-header-left">
                <IconKeyboard size={18} />
                <h2 className="ks-title">Keyboard Shortcuts</h2>
              </div>
              <button className="ks-close" onClick={onClose} aria-label="Close shortcuts">
                <IconX size={16} />
              </button>
            </div>
            <div className="ks-body">
              {SHORTCUTS.map((cat) => (
                <div key={cat.id} className="ks-category">
                  <h3 className="ks-category-title">{cat.label}</h3>
                  <div className="ks-items">
                    {cat.items.map((item, i) => (
                      <div key={i} className="ks-item">
                        <span className="ks-item-label">{item.label}</span>
                        <Kbd keys={item.keys} />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="ks-footer">
              <span className="ks-footer-text">Press <Kbd keys={['Esc']} /> to close</span>
            </div>
            <style>{ksCss}</style>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

const ksCss = `
.ks-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 200; padding: 16px; }
.ks-modal { background: #fff; border-radius: 16px; width: 520px; max-width: 100%; max-height: 80vh; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.12); }
.ks-header { display: flex; align-items: center; justify-content: space-between; padding: 18px 20px 12px; }
.ks-header-left { display: flex; align-items: center; gap: 10px; }
.ks-title { font-size: 16px; font-weight: 600; color: #1A1C1D; margin: 0; }
.ks-close { width: 32px; height: 32px; border-radius: 8px; border: none; background: transparent; cursor: pointer; display: flex; align-items: center; justify-content: center; color: rgba(26,28,29,0.4); transition: all 0.15s; }
.ks-close:hover { background: rgba(26,28,29,0.04); color: #1A1C1D; }
.ks-body { flex: 1; overflow-y: auto; padding: 4px 20px 12px; }
.ks-category { margin-bottom: 16px; }
.ks-category-title { font-size: 10px; font-weight: 600; color: rgba(26,28,29,0.4); text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 8px; }
.ks-items { display: flex; flex-direction: column; gap: 2px; }
.ks-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 6px; transition: background 0.15s; }
.ks-item:hover { background: rgba(26,28,29,0.03); }
.ks-item-label { font-size: 13px; color: #1A1C1D; }
.ks-kbd-group { display: inline-flex; align-items: center; gap: 2px; }
.ks-kbd { display: inline-flex; align-items: center; justify-content: center; padding: 2px 7px; min-width: 24px; height: 22px; border: 1px solid rgba(26,28,29,0.12); border-radius: 5px; background: rgba(255,255,255,0.8); font-size: 11px; font-family: 'SF Mono', 'Fira Code', monospace; color: rgba(26,28,29,0.6); box-shadow: 0 1px 0 rgba(0,0,0,0.04); }
.ks-kbd-plus { font-size: 10px; color: rgba(26,28,29,0.3); margin: 0 1px; }
.ks-footer { padding: 10px 20px 16px; border-top: 1px solid rgba(26,28,29,0.04); display: flex; justify-content: center; }
.ks-footer-text { font-size: 11px; color: rgba(26,28,29,0.35); display: flex; align-items: center; gap: 4px; }

@media (max-width: 480px) {
  .ks-modal { width: 100%; max-height: 90vh; border-radius: 12px; }
  .ks-body { padding: 4px 16px 12px; }
  .ks-header { padding: 14px 16px 10px; }
}
`;