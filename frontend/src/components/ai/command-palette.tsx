/**
 * Command Palette — Mantine Spotlight (Cmd+K)
 *
 * Global command palette for navigating SHUNYA spaces and asking the AI.
 * Dispatches a `shunya:action` CustomEvent on the window; the app shell's
 * PaletteActionsBridge (app.tsx) performs the navigation. Only actions with a
 * real surface are listed — a command that opens nothing is worse than an
 * absent one.
 */
import { Spotlight } from '@mantine/spotlight';
import {
  IconFileText,
  IconUser,
  IconMail,
  IconChecklist,
  IconHome,
  IconChartBar,
  IconSettings,
  IconRobot,
  IconBooks,
  IconHeartHandshake,
} from '@tabler/icons-react';
import { aiChat } from '../../api/ai-chat';
import '@mantine/spotlight/styles.css';

type PaletteAction = {
  id: string;
  label: string;
  description: string;
  leftSection: React.ReactNode;
  keywords?: string;
  onClick: () => void;
};

function dispatch(detail: string) {
  window.dispatchEvent(new CustomEvent('shunya:action', { detail }));
}

// ── AI query state ───────────────────────────────────────────────────

let _requestId = 0;

/** Dispatch shunya:ai-result events so the app shell can render results. */
function dispatchAiResult(status: 'loading' | 'done' | 'error', text: string,
                          query: string, requestId?: number) {
  window.dispatchEvent(new CustomEvent('shunya:ai-result', {
    detail: { status, text, query, requestId },
  }));
}

async function askAi(query: string): Promise<void> {
  const id = ++_requestId;
  dispatchAiResult('loading', '', query, id);
  try {
    const result = await aiChat(
      [{ role: 'user', content: query }],
      { webSearch: true, requestId: id },
    );
    if (result.error) {
      dispatchAiResult('error', result.error, query, id);
    } else {
      dispatchAiResult('done', result.content, query, id);
    }
  } catch (e: any) {
    dispatchAiResult('error', e?.message || 'Request failed', query, id);
  }
}

const navActions: PaletteAction[] = [
  {
    id: 'home',
    label: 'Home',
    description: 'Return to the unified dashboard',
    leftSection: <IconHome size={18} />,
    keywords: 'dashboard,start,overview',
    onClick: () => dispatch('home'),
  },
  {
    id: 'people',
    label: 'People',
    description: 'Open people, contacts and team members',
    leftSection: <IconUser size={18} />,
    keywords: 'customer,person,contacts,people',
    onClick: () => dispatch('people'),
  },
  {
    id: 'work',
    label: 'Work',
    description: 'Tasks, executions and SHUNYA work',
    leftSection: <IconChecklist size={18} />,
    keywords: 'todo,to-do,checklist,tasks',
    onClick: () => dispatch('work'),
  },
  {
    id: 'conversations',
    label: 'Conversations',
    description: 'All conversations and discussions',
    leftSection: <IconMail size={18} />,
    keywords: 'messages,discussion,thread',
    onClick: () => dispatch('conversations'),
  },
  {
    id: 'documents',
    label: 'Documents',
    description: 'Uploaded files, documents and records',
    leftSection: <IconFileText size={18} />,
    keywords: 'documents,uploads,storage,files',
    onClick: () => dispatch('documents'),
  },
  {
    id: 'knowledge',
    label: 'Knowledge',
    description: 'Docs, research and references',
    leftSection: <IconBooks size={18} />,
    keywords: 'research,library,notes',
    onClick: () => dispatch('knowledge'),
  },
  {
    id: 'relationships',
    label: 'Relationships',
    description: 'Connections between people and entities',
    leftSection: <IconHeartHandshake size={18} />,
    keywords: 'graph,links,network',
    onClick: () => dispatch('relationships'),
  },
  {
    id: 'team',
    label: 'Team',
    description: 'Invite and manage team members',
    leftSection: <IconUser size={18} />,
    keywords: 'members,invite,roles',
    onClick: () => dispatch('team'),
  },
  {
    id: 'analytics',
    label: 'Analytics',
    description: 'System analytics and dashboards',
    leftSection: <IconChartBar size={18} />,
    keywords: 'reports,charts,metrics,kpi,insights',
    onClick: () => dispatch('analytics'),
  },
  {
    id: 'import-export',
    label: 'Import & Export',
    description: 'Import records or export your data',
    leftSection: <IconFileText size={18} />,
    keywords: 'csv,export,import,migrate,backup',
    onClick: () => dispatch('import-export'),
  },
  {
    id: 'settings',
    label: 'Settings',
    description: 'Profile, security, and data',
    leftSection: <IconSettings size={18} />,
    keywords: 'preferences,config,security',
    onClick: () => dispatch('settings'),
  },
];

// ── Dynamic action list (navigation + AI query) ──────────────────────

/**
 * Ids dispatched by the static commands. Each one must resolve to a workspace
 * surface in `lib/palette-actions.ts` — asserted by
 * `lib/__tests__/palette-actions.test.ts`, so a command cannot ship without a
 * destination (the G1.25 defect: eleven commands dispatched into a void).
 */
export const PALETTE_ACTION_IDS: string[] = navActions.map((a) => a.id);

function aiAction(query: string): any {
  return {
    id: 'ask-ai',
    label: `Ask AI: ${query}`,
    description: 'Send this query to the SHUNYA AI assistant',
    leftSection: <IconRobot size={18} />,
    onClick: (() => { askAi(query); }) as any,
  };
}

/**
 * Spotlight filter.
 *
 * G1.27: this used to return the *entire* action list whenever the query matched
 * any command, so typing "Settings" left all commands visible and Enter
 * activated whichever sat first — the search field filtered nothing. It now
 * filters for real:
 *
 *   - empty query            → the full command list
 *   - query matches commands → only the matching commands (a 3+ word phrase is
 *                              treated as a question and offers the AI first)
 *   - query matches nothing  → a single "Ask AI: …" row, not a wall of
 *                              unrelated commands
 *
 * It always returns a NEW array (never mutates `actions`) — mutating it made
 * Mantine accumulate duplicate `ask-ai` keys on every keystroke.
 */
function actionsFor(query: string, actions: any[]): any[] {
  const trimmed = query.trim();
  if (!trimmed) return actions;

  const ql = trimmed.toLowerCase();
  const matched = actions.filter((a) =>
    (a.label || '').toLowerCase().includes(ql) ||
    (a.keywords || '').toLowerCase().includes(ql),
  );
  const looksLikeQuestion = trimmed.split(/\s+/).length >= 3;

  if (looksLikeQuestion) return [aiAction(trimmed), ...matched];
  if (matched.length === 0) return [aiAction(trimmed)];
  return matched;
}

const allActions = [...navActions];

export function CommandPalette() {
  return (
    <Spotlight
      actions={allActions}
      filter={actionsFor}
      searchProps={{ placeholder: 'Search commands or ask a question...' }}
      shortcut="mod + k"
      nothingFound="No results found"
      highlightQuery
      limit={7}
      scrollable
      maxHeight={400}
    />
  );
}