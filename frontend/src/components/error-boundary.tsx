/**
 * ErrorBoundary — Catches React render errors and shows a friendly fallback.
 *
 * Wraps the active space panel content so React #130 ("Element type is invalid")
 * crashes during rapid panel switching don't take down the entire page.
 *
 * Warm glass-morphism design matching the SHUNYA OS aesthetic.
 */

import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="un-error-boundary">
            <div className="un-error-boundary-icon">⚠</div>
            <p className="un-error-boundary-text">Something went wrong with this panel.</p>
            <p className="un-error-boundary-detail">{this.state.error?.message || 'Unknown error'}</p>
            <button className="un-error-boundary-btn" onClick={() => this.setState({ hasError: false, error: null })}>
              Retry
            </button>
            <style>{errorBoundaryStyles}</style>
          </div>
        )
      );
    }
    return this.props.children;
  }
}

const errorBoundaryStyles = `
.un-error-boundary {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 24px;
  min-height: 200px;
  text-align: center;
}
.un-error-boundary-icon {
  font-size: 32px;
  opacity: 0.4;
}
.un-error-boundary-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--sh-text, #1A1C1D);
  margin: 0;
}
.un-error-boundary-detail {
  font-size: 11px;
  color: rgba(26,28,29,0.45);
  max-width: 300px;
  line-height: 1.5;
  margin: 0;
}
.un-error-boundary-btn {
  padding: 8px 20px;
  background: linear-gradient(135deg, #6C4AE2, #A4865F);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.15s;
}
.un-error-boundary-btn:hover {
  opacity: 0.9;
}
`;
