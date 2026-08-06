/**
 * Token Provider — React component that delivers tokens to the browser.
 *
 * Only file in the token system that imports React.
 * Uses the framework-independent definition module for token values.
 * Light mode only.
 */

import { createContext, useContext, useMemo, type ReactNode } from 'react';
import { cssVariables } from './definitions';

const TokenCtx = createContext<Record<string, never>>({});

export const useToken = () => useContext(TokenCtx);

export function TokenProvider({ children }: { children: ReactNode }) {
  const css = useMemo(() => cssVariables(), []);

  return (
    <TokenCtx.Provider value={{}}>
      <style>{css}</style>
      {children}
    </TokenCtx.Provider>
  );
}
