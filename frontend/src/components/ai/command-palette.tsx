/**
 * Command Palette — Mantine Spotlight (Cmd+K)
 *
 * Global command palette for navigating SHUNYA spaces, creating objects,
 * and toggling theme. Dispatch a `shunya:action` CustomEvent on the window
 * that the unified OS surface listens for to run the action.
 */
import { Spotlight } from '@mantine/spotlight';
import {
  IconSearch,
  IconFileText,
  IconInvoice,
  IconUser,
  IconCalendar,
  IconMail,
  IconChecklist,
  IconMoon,
  IconHome,
  IconChartBar,
  IconSettings,
  IconRobot,
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

let _aiResult: { status: 'idle' | 'loading' | 'done' | 'error'; text: string }
    = { status: 'idle', text: '' };

/** Exposed so callers can render AI results outside the palette. */
export function getAiResult() { return _aiResult; }

/** Called before opening the palette to reset AI state. */
export function resetAiResult() {
  _aiResult = { status: 'idle', text: '' };
}

async function askAi(query: string): Promise<void> {
  _aiResult = { status: 'loading', text: '' };
  try {
    const result = await aiChat(
      [{ role: 'user', content: query }],
      { webSearch: true },
    );
    _aiResult = result.error
      ? { status: 'error', text: result.error }
      : { status: 'done', text: result.content };
  } catch (e: any) {
    _aiResult = { status: 'error', text: e?.message || 'Request failed' };
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
    id: 'new-proposal',
    label: 'New Proposal',
    description: 'Create a new proposal',
    leftSection: <IconFileText size={18} />,
    keywords: 'quote,estimate,rfp',
    onClick: () => dispatch('proposals'),
  },
  {
    id: 'new-invoice',
    label: 'New Invoice',
    description: 'Create a new invoice',
    leftSection: <IconInvoice size={18} />,
    keywords: 'bill,payment',
    onClick: () => dispatch('invoices'),
  },
  {
    id: 'new-contact',
    label: 'New Contact',
    description: 'Add a new contact',
    leftSection: <IconUser size={18} />,
    keywords: 'customer,person,people',
    onClick: () => dispatch('contacts'),
  },
  {
    id: 'tasks',
    label: 'Tasks',
    description: 'View and manage tasks',
    leftSection: <IconChecklist size={18} />,
    keywords: 'todo,to-do,checklist',
    onClick: () => dispatch('tasks'),
  },
  {
    id: 'calendar',
    label: 'Calendar',
    description: 'View calendar',
    leftSection: <IconCalendar size={18} />,
    keywords: 'schedule,events,meetings',
    onClick: () => dispatch('calendar'),
  },
  {
    id: 'email',
    label: 'Email',
    description: 'Open email inbox',
    leftSection: <IconMail size={18} />,
    keywords: 'inbox,mail,message',
    onClick: () => dispatch('email'),
  },
  {
    id: 'files',
    label: 'File Manager',
    description: 'Browse uploaded files',
    leftSection: <IconSearch size={18} />,
    keywords: 'documents,uploads,storage',
    onClick: () => dispatch('files'),
  },
  {
    id: 'settings',
    label: 'Settings',
    description: 'Profile, appearance, and data',
    leftSection: <IconSettings size={18} />,
    keywords: 'preferences,config',
    onClick: () => dispatch('settings'),
  },
  {
    id: 'analytics',
    label: 'Analytics',
    description: 'View business insights',
    leftSection: <IconChartBar size={18} />,
    keywords: 'reports,charts,metrics,kpi',
    onClick: () => dispatch('business'),
  },
  {
    id: 'dark-mode',
    label: 'Toggle Dark Mode',
    description: 'Switch between light and dark',
    leftSection: <IconMoon size={18} />,
    keywords: 'theme,light,dark,appearance',
    onClick: () => dispatch('toggle-dark'),
  },
];

// ── Dynamic action list (navigation + AI query) ──────────────────────

function actionsFor(query: string, actions: any[]): any[] {
  const trimmed = query.trim();
  if (trimmed.length > 0) {
    const ql = trimmed.toLowerCase();
    const alreadyMatched = navActions.some(a =>
      a.label.toLowerCase().includes(ql) ||
      (a.keywords && a.keywords.toLowerCase().includes(ql))
    );
    if (!alreadyMatched || trimmed.split(/\s+/).length >= 3) {
      // Prepend AI action — Spotlight displays it first.
      actions.unshift({
        id: 'ask-ai',
        label: `Ask AI: ${trimmed}`,
        description: 'Send this query to the SHUNYA AI assistant',
        leftSection: <IconRobot size={18} />,
        onClick: (() => { askAi(trimmed); }) as any,
      });
    }
  }
  return actions;
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