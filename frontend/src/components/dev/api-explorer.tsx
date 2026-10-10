/**
 * API Explorer / Docs — static doc page listing API endpoints by domain.
 *
 * Uses existing route patterns from app/__init__.py blueprint registrations.
 * No backend needed — purely documentation.
 */
import { useState } from 'react';
import {
  IconApi, IconLock, IconCode, IconChevronDown, IconChevronRight,
  IconCopy, IconCheck,
} from '@tabler/icons-react';

interface Endpoint {
  method: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  path: string;
  description: string;
  example?: string;
  auth?: string;
}

interface Domain {
  id: string;
  label: string;
  icon: string;
  description: string;
  endpoints: Endpoint[];
}

const API_DOMAINS: Domain[] = [
  {
    id: 'auth',
    label: 'Auth',
    icon: '🔐',
    description: 'Authentication, session management, and identity',
    endpoints: [
      { method: 'POST', path: '/api/v1/auth/login', description: 'Authenticate a user with email/password', example: 'curl -X POST /api/v1/auth/login -H "Content-Type: application/json" -d \'{"email":"user@example.com","password":"..."}\'' },
      { method: 'POST', path: '/api/v1/auth/logout', description: 'End the current session', example: 'curl -X POST /api/v1/auth/logout' },
      { method: 'GET', path: '/api/v1/auth/me', description: 'Get current authenticated user profile', example: 'curl /api/v1/auth/me' },
      { method: 'POST', path: '/api/v1/auth/register', description: 'Register a new user account', example: 'curl -X POST /api/v1/auth/register -H "Content-Type: application/json" -d \'{"email":"user@example.com","password":"..."}\'' },
    ],
  },
  {
    id: 'workspaces',
    label: 'Workspaces',
    icon: '📋',
    description: 'Workspace CRUD and navigation context',
    endpoints: [
      { method: 'GET', path: '/api/v1/workspace', description: 'Get current workspace context', example: 'curl /api/v1/workspace' },
      { method: 'PATCH', path: '/api/v1/workspace', description: 'Update workspace settings', example: 'curl -X PATCH /api/v1/workspace -H "Content-Type: application/json" -d \'{"name":"My Workspace"}\'' },
      { method: 'GET', path: '/api/v1/workspace/objects/:id', description: 'Get unified workspace context for an object', example: 'curl /api/v1/workspace/objects/obj_123?type=contact' },
      { method: 'GET', path: '/api/v1/workspace/timeline', description: 'Get timeline for a context', example: 'curl "/api/v1/workspace/timeline?object_type=contact&object_id=obj_123"' },
      { method: 'POST', path: '/api/v1/workspace/copilot/ask', description: 'Ask SHUNYA a contextual question', example: 'curl -X POST /api/v1/workspace/copilot/ask -H "Content-Type: application/json" -d \'{"query":"What do we know about this contact?","object_type":"contact","object_id":"obj_123"}\'' },
    ],
  },
  {
    id: 'objects',
    label: 'Universal Objects',
    icon: '📦',
    description: 'CRUD operations on universal SHUNYA objects',
    endpoints: [
      { method: 'GET', path: '/api/v1/objects', description: 'List objects with type filtering and pagination', example: 'curl "/api/v1/objects?type=contact&limit=20&offset=0"' },
      { method: 'POST', path: '/api/v1/objects', description: 'Create a new object', example: 'curl -X POST /api/v1/objects -H "Content-Type: application/json" -d \'{"object_type":"contact","name":"Jane Doe"}\'' },
      { method: 'GET', path: '/api/v1/objects/:id', description: 'Get a single object by ID', example: 'curl /api/v1/objects/obj_123' },
      { method: 'PATCH', path: '/api/v1/objects/:id', description: 'Update an object', example: 'curl -X PATCH /api/v1/objects/obj_123 -H "Content-Type: application/json" -d \'{"name":"Jane Smith"}\'' },
      { method: 'DELETE', path: '/api/v1/objects/:id', description: 'Delete an object', example: 'curl -X DELETE /api/v1/objects/obj_123' },
      { method: 'GET', path: '/api/v1/objects/types', description: 'List object types with counts', example: 'curl /api/v1/objects/types' },
    ],
  },
  {
    id: 'relationships',
    label: 'Relationships',
    icon: '🔗',
    description: 'Relationship graph between people, entities, and objects',
    endpoints: [
      { method: 'GET', path: '/api/v1/relationships', description: 'List relationships with optional type filter', example: 'curl "/api/v1/relationships?type=business"' },
      { method: 'POST', path: '/api/v1/relationships', description: 'Create a relationship between two objects', example: 'curl -X POST /api/v1/relationships -H "Content-Type: application/json" -d \'{"source_id":"obj_1","target_id":"obj_2","relationship_type":"works_with"}\'' },
      { method: 'GET', path: '/api/v1/relationships/:id', description: 'Get a single relationship with timeline', example: 'curl /api/v1/relationships/123' },
      { method: 'PATCH', path: '/api/v1/relationships/:id', description: 'Update relationship properties', example: 'curl -X PATCH /api/v1/relationships/123 -H "Content-Type: application/json" -d \'{"strength":"strong"}\'' },
    ],
  },
  {
    id: 'documents',
    label: 'Documents',
    icon: '📄',
    description: 'Document ingestion, management, and intelligence',
    endpoints: [
      { method: 'GET', path: '/api/v1/documents', description: 'List uploaded documents', example: 'curl /api/v1/documents' },
      { method: 'POST', path: '/api/v1/documents/upload', description: 'Upload a document file', example: 'curl -X POST /api/v1/documents/upload -F "file=@report.pdf"' },
      { method: 'GET', path: '/api/v1/documents/:id', description: 'Get document details and extracted content', example: 'curl /api/v1/documents/doc_123' },
      { method: 'DELETE', path: '/api/v1/documents/:id', description: 'Delete a document', example: 'curl -X DELETE /api/v1/documents/doc_123' },
      { method: 'POST', path: '/api/v1/documents/knowledge/extract', description: 'Extract knowledge from a document', example: 'curl -X POST /api/v1/documents/knowledge/extract -H "Content-Type: application/json" -d \'{"document_id":"doc_123"}\'' },
    ],
  },
  {
    id: 'ai',
    label: 'AI Intelligence',
    icon: '🧠',
    description: 'AI chat, reasoning, execution, and intelligence pipeline',
    endpoints: [
      { method: 'POST', path: '/api/v1/ai/chat', description: 'Chat with SHUNYA AI', example: 'curl -X POST /api/v1/ai/chat -H "Content-Type: application/json" -d \'{"message":"What tasks are pending?","session_id":"sess_123"}\'' },
      { method: 'POST', path: '/api/v1/intention', description: 'Get SHUNYA\'s current intention/recommendation', example: 'curl /api/v1/intention' },
      { method: 'POST', path: '/api/v1/search', description: 'Universal search across all objects and documents', example: 'curl -X POST /api/v1/search -H "Content-Type: application/json" -d \'{"query":"meeting notes","limit":10}\'' },
      { method: 'GET', path: '/api/v1/analytics/dashboard', description: 'Get analytics dashboard data', example: 'curl /api/v1/analytics/dashboard' },
      { method: 'GET', path: '/api/v1/objects/:id/insights', description: 'Get AI insights for a specific object', example: 'curl /api/v1/objects/obj_123/insights' },
    ],
  },
  {
    id: 'commercial',
    label: 'Commercial',
    icon: '💰',
    description: 'Revenue, opportunities, proposals, and pipeline',
    endpoints: [
      { method: 'GET', path: '/api/v1/commercial/opportunities', description: 'List commercial opportunities', example: 'curl /api/v1/commercial/opportunities' },
      { method: 'POST', path: '/api/v1/commercial/opportunities', description: 'Create a new opportunity', example: 'curl -X POST /api/v1/commercial/opportunities -H "Content-Type: application/json" -d \'{"name":"New Deal","amount":50000}\'' },
      { method: 'GET', path: '/api/v1/commercial/proposals', description: 'List proposals', example: 'curl /api/v1/commercial/proposals' },
      { method: 'GET', path: '/api/v1/commercial/pipeline', description: 'Get pipeline summary with stages', example: 'curl /api/v1/commercial/pipeline' },
    ],
  },
  {
    id: 'execution',
    label: 'Execution',
    icon: '⚡',
    description: 'Tasks, commitments, execution chains, and outcomes',
    endpoints: [
      { method: 'GET', path: '/api/v1/commitments', description: 'List commitments with status filters', example: 'curl /api/v1/commitments' },
      { method: 'POST', path: '/api/v1/commitments', description: 'Create a new commitment/task', example: 'curl -X POST /api/v1/commitments -H "Content-Type: application/json" -d \'{"title":"Review Q3 report","owner":"self"}\'' },
      { method: 'POST', path: '/api/v1/commitments/:id/transition', description: 'Transition commitment status', example: 'curl -X POST /api/v1/commitments/123/transition -H "Content-Type: application/json" -d \'{"status":"completed","evidence":"Report reviewed and approved"}\'' },
      { method: 'GET', path: '/api/v1/executions', description: 'List execution history', example: 'curl /api/v1/executions' },
      { method: 'GET', path: '/api/v1/outcomes', description: 'List business outcomes', example: 'curl /api/v1/outcomes' },
    ],
  },
  {
    id: 'memory',
    label: 'Memory & Knowledge',
    icon: '🧩',
    description: 'Persistent memory, knowledge extraction, and facts',
    endpoints: [
      { method: 'POST', path: '/api/v1/memory/store', description: 'Store a memory fragment', example: 'curl -X POST /api/v1/memory/store -H "Content-Type: application/json" -d \'{"key":"preference_timezone","content":"UTC+5:30"}\'' },
      { method: 'GET', path: '/api/v1/memory/search', description: 'Search stored memories', example: 'curl "/api/v1/memory/search?q=preference"' },
      { method: 'GET', path: '/api/v1/knowledge', description: 'List knowledge documents', example: 'curl /api/v1/knowledge' },
      { method: 'POST', path: '/api/v1/knowledge/extract', description: 'Extract knowledge facts from text', example: 'curl -X POST /api/v1/knowledge/extract -H "Content-Type: application/json" -d \'{"text":"...","source":"manual"}\'' },
    ],
  },
  {
    id: 'health',
    label: 'System',
    icon: '🔧',
    description: 'Health checks, metrics, and system diagnostics',
    endpoints: [
      { method: 'GET', path: '/health', description: 'Full health check (DB, services, versions)', example: 'curl /health' },
      { method: 'GET', path: '/ready', description: 'Readiness probe', example: 'curl /ready' },
      { method: 'GET', path: '/live', description: 'Liveness probe', example: 'curl /live' },
      { method: 'GET', path: '/metrics', description: 'Prometheus-format metrics', example: 'curl /metrics' },
    ],
  },
];

function MethodBadge({ method }: { method: Endpoint['method'] }) {
  const colors: Record<string, string> = {
    GET: '#2D6A4F',
    POST: '#6C4AE2',
    PATCH: '#E67E22',
    PUT: '#0891B2',
    DELETE: '#B91C1C',
  };
  return (
    <span className="ae-method" style={{ background: `${colors[method] || '#666'}14`, color: colors[method] || '#666' }}>
      {method}
    </span>
  );
}

function EndpointRow({ ep }: { ep: Endpoint }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyExample = () => {
    if (!ep.example) return;
    navigator.clipboard.writeText(ep.example);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`ae-endpoint ${expanded ? 'ae-endpoint-expanded' : ''}`}>
      <button className="ae-endpoint-header" onClick={() => setExpanded(!expanded)}>
        <span className="ae-expand-icon">{expanded ? <IconChevronDown size={12} /> : <IconChevronRight size={12} />}</span>
        <MethodBadge method={ep.method} />
        <code className="ae-path">{ep.path}</code>
        <span className="ae-desc">{ep.description}</span>
        {ep.auth && <span className="ae-auth"><IconLock size={10} /> {ep.auth}</span>}
      </button>
      {expanded && ep.example && (
        <div className="ae-example">
          <div className="ae-example-header">
            <span className="ae-example-title"><IconCode size={12} /> Example</span>
            <button className="ae-copy-btn" onClick={copyExample}>
              {copied ? <IconCheck size={12} /> : <IconCopy size={12} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <pre className="ae-example-code">{ep.example}</pre>
        </div>
      )}
    </div>
  );
}

function DomainSection({ domain }: { domain: Domain }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="ae-domain">
      <button className="ae-domain-header" onClick={() => setExpanded(!expanded)}>
        <span className="ae-domain-icon">{domain.icon}</span>
        <span className="ae-domain-label">{domain.label}</span>
        <span className="ae-domain-count">{domain.endpoints.length} endpoints</span>
        <span className="ae-domain-expand">{expanded ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}</span>
      </button>
      <p className="ae-domain-desc">{domain.description}</p>
      {expanded && (
        <div className="ae-endpoints">
          {domain.endpoints.map((ep, i) => (
            <EndpointRow key={i} ep={ep} />
          ))}
        </div>
      )}
    </div>
  );
}

export function ApiExplorer() {
  return (
    <div className="ae-container">
      <div className="ae-header">
        <div className="ae-header-icon"><IconApi size={22} /></div>
        <div>
          <h2 className="ae-title">API Documentation</h2>
          <p className="ae-subtitle">Explore available API endpoints by domain — {API_DOMAINS.reduce((s, d) => s + d.endpoints.length, 0)} total</p>
        </div>
      </div>
      <p className="ae-note">All endpoints require authentication via session cookie or <code>X-Identity-Id</code> header unless marked public.</p>
      {API_DOMAINS.map((domain) => (
        <DomainSection key={domain.id} domain={domain} />
      ))}
      <style>{aeCss}</style>
    </div>
  );
}

const aeCss = `
.ae-container { display: flex; flex-direction: column; gap: 8px; padding: 32px; max-width: 800px; }
.ae-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.ae-header-icon { width: 40px; height: 40px; border-radius: 12px; background: rgba(164,134,95,0.10); color: #A4865F; display: flex; align-items: center; justify-content: center; }
.ae-title { font-size: 18px; font-weight: 600; color: #1A1C1D; margin: 0; }
.ae-subtitle { font-size: 12px; color: rgba(26,28,29,0.45); margin: 2px 0 0; }
.ae-note { font-size: 12px; color: rgba(26,28,29,0.45); padding: 10px 14px; background: rgba(164,134,95,0.06); border-radius: 8px; margin: 0; }
.ae-note code { font-size: 11px; background: rgba(26,28,29,0.06); padding: 1px 5px; border-radius: 3px; }

.ae-domain { background: rgba(255,255,255,0.6); border: 1px solid rgba(26,28,29,0.06); border-radius: 10px; overflow: hidden; }
.ae-domain-header { display: flex; align-items: center; gap: 8px; width: 100%; padding: 12px 14px; border: none; background: transparent; cursor: pointer; text-align: left; font-family: inherit; color: #1A1C1D; transition: background 0.15s; }
.ae-domain-header:hover { background: rgba(26,28,29,0.02); }
.ae-domain-icon { font-size: 16px; }
.ae-domain-label { font-size: 14px; font-weight: 600; flex: 1; }
.ae-domain-count { font-size: 11px; color: rgba(26,28,29,0.4); margin-right: 8px; }
.ae-domain-expand { font-size: 12px; color: rgba(26,28,29,0.3); }
.ae-domain-desc { font-size: 12px; color: rgba(26,28,29,0.5); padding: 0 14px 10px; margin: -4px 0 0; }

.ae-endpoints { border-top: 1px solid rgba(26,28,29,0.04); }
.ae-endpoint { border-bottom: 1px solid rgba(26,28,29,0.03); }
.ae-endpoint:last-child { border-bottom: none; }
.ae-endpoint-header { display: flex; align-items: center; gap: 8px; width: 100%; padding: 10px 14px; border: none; background: transparent; cursor: pointer; text-align: left; font-family: inherit; transition: background 0.15s; }
.ae-endpoint-header:hover { background: rgba(26,28,29,0.02); }
.ae-expand-icon { font-size: 10px; color: rgba(26,28,29,0.3); flex-shrink: 0; width: 14px; text-align: center; }
.ae-method { display: inline-flex; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: 0.04em; font-family: 'SF Mono', 'Fira Code', monospace; flex-shrink: 0; min-width: 44px; justify-content: center; }
.ae-path { font-size: 12px; font-family: 'SF Mono', 'Fira Code', monospace; color: #1A1C1D; flex-shrink: 0; }
.ae-desc { font-size: 12px; color: rgba(26,28,29,0.5); flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ae-auth { display: inline-flex; align-items: center; gap: 3px; font-size: 10px; color: rgba(26,28,29,0.35); flex-shrink: 0; }

.ae-example { padding: 0 14px 12px 42px; }
.ae-example-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.ae-example-title { display: flex; align-items: center; gap: 4px; font-size: 10px; font-weight: 600; color: rgba(26,28,29,0.4); text-transform: uppercase; letter-spacing: 0.06em; }
.ae-copy-btn { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border: 1px solid rgba(26,28,29,0.06); border-radius: 4px; background: transparent; font-size: 10px; color: rgba(26,28,29,0.4); cursor: pointer; font-family: inherit; transition: all 0.15s; }
.ae-copy-btn:hover { border-color: #A4865F; color: #A4865F; }
.ae-example-code { font-size: 11px; font-family: 'SF Mono', 'Fira Code', monospace; background: rgba(26,28,29,0.03); border: 1px solid rgba(26,28,29,0.04); border-radius: 6px; padding: 10px 12px; margin: 0; overflow-x: auto; color: rgba(26,28,29,0.7); line-height: 1.5; white-space: pre-wrap; word-break: break-all; }

@media (max-width: 480px) {
  .ae-container { padding: 20px; }
  .ae-endpoint-header { flex-wrap: wrap; gap: 4px; }
  .ae-desc { width: 100%; margin-left: 34px; }
  .ae-example { padding-left: 14px; }
}
`;