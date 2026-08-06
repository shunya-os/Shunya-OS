/**
 * ErrorFallback — Universal error recovery component.
 * Every component uses this for consistent error display.
 *
 * Usage:
 *   if (error) return <ErrorFallback message={error} onRetry={refetch} />;
 */
import { RefreshCw, ExternalLink } from 'lucide-react';

interface ErrorFallbackProps {
  message: string;
  onRetry?: () => void;
  details?: string;
  url?: string; // for iframe errors — "Open in new tab" button
}

export function ErrorFallback({ message, onRetry, details, url }: ErrorFallbackProps) {
  return (
    <div className="un-error-fallback">
      <div className="un-error-fallback-icon">⚠</div>
      <h3 className="un-error-fallback-title">{message}</h3>
      {details && <p className="un-error-fallback-details">{details}</p>}
      <div className="un-error-fallback-actions">
        {url && (
          <a href={url} target="_blank" rel="noopener noreferrer" className="un-btn un-btn-primary">
            <ExternalLink size={14} />
            Open in new tab
          </a>
        )}
        {onRetry && (
          <button className="un-btn un-btn-ghost" onClick={onRetry}>
            <RefreshCw size={14} />
            Retry
          </button>
        )}
      </div>
      <style>{`
        .un-error-fallback { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; text-align: center; gap: 12px; }
        .un-error-fallback-icon { font-size: 40px; }
        .un-error-fallback-title { color: var(--sh-text, #1A1C1D); font-size: 18px; font-weight: 500; margin: 0; }
        .un-error-fallback-details { color: var(--sh-text-secondary, #6B5B3E); font-size: 14px; margin: 0; max-width: 400px; }
        .un-error-fallback-actions { display: flex; gap: 12px; margin-top: 8px; }
        .un-error-fallback-actions .un-btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; text-decoration: none; }
        [data-theme="dark"] .un-error-fallback-title { color: #FAF8F5; }
        [data-theme="dark"] .un-error-fallback-details { color: #C4B89A; }
      `}</style>
    </div>
  );
}