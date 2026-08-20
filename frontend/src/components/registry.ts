/**
 * Component Registry — Single place where all components are registered.
 *
 * Enables discovery, documentation generation, and future dynamic loading.
 */

import type { ComponentType } from 'react';
import type { ComponentProps } from './executive/index';
import {
  Metric,
  Badge,
  StatusDot,
  ObjectIdentity,
  TimelineEvent,
  InsightCard,
  ProgressBar,
  ConfidenceMeter,
  BlockerList,
  NextBestAction,
  ConversationCard,
  Panel,
} from './executive/index';
import { CommercialContext } from './commercial/commercial-context';

export interface ComponentMeta {
  id: string;
  name: string;
  description: string;
  category: 'primitive' | 'object' | 'commitment' | 'conversation' | 'layout';
  component: ComponentType<ComponentProps<any>>;
  propsSchema: Record<string, string>;
}

export const componentRegistry: ComponentMeta[] = [
  {
    id: 'metric',
    name: 'Metric',
    description: 'Single numeric value with optional trend',
    category: 'primitive',
    component: Metric,
    propsSchema: { value: 'string|number', trend: 'number?', subtitle: 'string?' },
  },
  {
    id: 'badge',
    name: 'Badge',
    description: 'Small status or category label',
    category: 'primitive',
    component: Badge,
    propsSchema: { text: 'string', variant: 'success|warning|danger|neutral|info?' },
  },
  {
    id: 'status-dot',
    name: 'Status Dot',
    description: 'Coloured dot indicating status',
    category: 'primitive',
    component: StatusDot,
    propsSchema: { status: 'string', label: 'string?' },
  },
  {
    id: 'object-identity',
    name: 'Object Identity',
    description: 'Object name, type, status, and ID',
    category: 'object',
    component: ObjectIdentity,
    propsSchema: { name: 'string', type: 'string', status: 'string', id: 'string' },
  },
  {
    id: 'timeline-event',
    name: 'Timeline Event',
    description: 'Single event with impact indicator',
    category: 'object',
    component: TimelineEvent,
    propsSchema: {
      title: 'string',
      description: 'string?',
      timestamp: 'number',
      type: 'string',
      commitmentImpact: 'string?',
    },
  },
  {
    id: 'insight-card',
    name: 'Insight Card',
    description: 'AI insight with confidence badge',
    category: 'object',
    component: InsightCard,
    propsSchema: { title: 'string', body: 'string', confidence: 'high|medium|low', type: 'string' },
  },
  {
    id: 'progress-bar',
    name: 'Progress Bar',
    description: 'Horizontal progress indicator',
    category: 'commitment',
    component: ProgressBar,
    propsSchema: { value: 'number', max: 'number?', label: 'string?' },
  },
  {
    id: 'confidence-meter',
    name: 'Confidence Meter',
    description: 'Explainable confidence score',
    category: 'commitment',
    component: ConfidenceMeter,
    propsSchema: { score: 'number', factors: 'string[]?' },
  },
  {
    id: 'blocker-list',
    name: 'Blocker List',
    description: 'List of active blockers by severity',
    category: 'commitment',
    component: BlockerList,
    propsSchema: { blockers: 'array' },
  },
  {
    id: 'next-best-action',
    name: 'Next Best Action',
    description: 'AI-suggested next action',
    category: 'commitment',
    component: NextBestAction,
    propsSchema: { action: 'string', reason: 'string', confidence: 'string' },
  },
  {
    id: 'conversation-card',
    name: 'Conversation Card',
    description: 'Conversation summary with context',
    category: 'conversation',
    component: ConversationCard,
    propsSchema: {
      title: 'string',
      intent: 'string',
      status: 'string',
      participants: 'string[]',
      objectCount: 'number',
    },
  },
  {
    id: 'panel',
    name: 'Panel',
    description: 'Layout panel with header and body',
    category: 'layout',
    component: Panel as any,
    propsSchema: { id: 'string', name: 'string' },
  },
  {
    id: 'commercial-context',
    name: 'Commercial Context Panel',
    description: 'Commercial context for a relationship — what matters right now',
    category: 'layout',
    component: CommercialContext as any,
    propsSchema: { relationshipId: 'number|string', organizationId: 'number?' },
  },
];

export function getComponent(id: string): ComponentMeta | undefined {
  return componentRegistry.find((c) => c.id === id);
}

export function getComponentsByCategory(category: string): ComponentMeta[] {
  return componentRegistry.filter((c) => c.category === category);
}
