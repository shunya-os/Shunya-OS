/**
 * Token Provider — React component that delivers tokens to the browser.
 *
 * Only file in the token system that imports React.
 * Uses the framework-independent definition module for token values.
 */

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { cssVariables } from './definitions';

type Theme = 'light' | 'dark';

const TokenCtx = createContext<{ theme: Theme; setTheme: (t: Theme) => void }>({ theme: 'light', setTheme: () => {} });

export const useToken = () => useContext(TokenCtx);

function prefer(): Theme {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function TokenProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(prefer);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => setTheme(e.matches ? 'dark' : 'light');
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const css = useMemo(() => cssVariables(theme), [theme]);

  return (
    <TokenCtx.Provider value={{ theme, setTheme }}>
      <style>{css}</style>
      <div className={`shunya-theme-${theme}`}>{children}</div>
    </TokenCtx.Provider>
  );
}