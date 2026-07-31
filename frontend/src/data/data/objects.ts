// SHUNYA Frontend — Demo Data
// Business-agnostic objects for the runtime

export const OBJECTS: Record<string, any> = {
  'obj-0042': {
    id: 'OBJ-0042',
    type: 'Decision',
    typeIcon: '⚖',
    name: 'Budget Increase Q3 Marketing',
    status: { label: 'Pending Approval', class: 'pending' },
    confidence: 0.42,
    confidenceLevel: 'moderate',
    summary: 'This decision recommends a 15% budget increase for Q3 marketing, citing 22% ROI on similar campaigns last year.\n\nAwaiting CFO approval. The proposed increase aligns with Q2 performance trends and the annual growth target.',
    identity: {
      name: 'Budget Increase Q3 Marketing', type: 'Decision', id: 'OBJ-0042',
      status: 'Pending Approval', createdBy: 'Jane Smith', createdAt: '2026-07-20 14:30',
      updatedBy: 'Mark Chen', updatedAt: '2026-07-22 09:15',
      tags: ['budget', 'marketing', 'Q3', 'growth'],
    },
    timeline: [
      { date: 'Today', events: [
        { time: '09:15', text: 'Status changed to Pending Approval', actor: 'Mark Chen' },
        { time: '08:30', text: 'Document attached: Q2 Performance Report', actor: 'Jane Smith' },
      ]},
      { date: 'Yesterday', events: [
        { time: '14:30', text: 'Object created', actor: 'Jane Smith' },
      ]},
    ],
    suggestions: [
      { id: 's1', text: 'Approve — the evidence is consistent with past successful decisions.', confidence: 0.72, sourceCount: 3, dismissed: false },
      { id: 's2', text: 'Review the ROI Impact Assessment before approving.', confidence: 0.65, sourceCount: 2, dismissed: false },
    ],
  },
  'obj-0043': {
    id: 'OBJ-0043',
    type: 'Project',
    typeIcon: '◆',
    name: 'Q3 Planning Initiative',
    status: { label: 'Active', class: 'active' },
    confidence: 0.85,
    confidenceLevel: 'high',
    summary: 'Coordinates all departmental budgets and growth targets for Q3 2026. Currently in active planning phase with 4 sub-projects.',
    suggestions: [
      { id: 's3', text: 'Two milestones are approaching — consider scheduling a review.', confidence: 0.88, sourceCount: 2, dismissed: false },
    ],
  },
};

export const RECENT_ITEMS = [
  { id: 'obj-0042', name: 'Budget Increase Q3 Marketing', type: 'Decision', icon: '⚖' },
  { id: 'obj-0043', name: 'Q3 Planning Initiative', type: 'Project', icon: '◆' },
];