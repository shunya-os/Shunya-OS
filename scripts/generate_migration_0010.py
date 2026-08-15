"""
Generate migration 0010 — safe IF NOT EXISTS table creation for all model tables.
Reads SQLAlchemy metadata after importing all models.
No database connection.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TESTING"] = True

from app import db
db.init_app(app)

# ===== Import ALL model modules to register tables =====

from app.models import (
    Lead, Supplier, InvoiceStatus, TaskList, Task, Person,
    Notification, Document, ActivityLog, Celebration,
    IntakeSession, IntakeCandidate, IntakeFieldMapping,
    Organization, OrgMember, OrgInvitation, Department,
    Proposal, ProposalVersion, KnowledgeDocument,
    PersonIdentity,
)
from app.tenant import Tenant, TenantTheme
from app.auth import TeamMember, PasswordResetToken, EmailVerificationToken, InvitationToken
from app.authz.models import Role, OrgMemberRole
from app.authz.extended_models import ServiceAccount, ApprovalDelegation, TenantPolicy
from app.security.audit import AuditLog  # noqa: F401 — table: sh_audit_logs
from app.evidence.models_db import EvidenceRecord
from app.evidence.decision_trace import DecisionTrace
from app.evidence.models import (  # dummy stubs but register tables
    SourceReference, EvidenceLink, AssertionRecord, SourceAssessment,
)
from app.automation.models import AutomationRule, AutomationLog
from app.intelligence.memory_store import LearningWeight
from app.intelligence.models import (ReasoningTrace, LearningEvent, AnomalyRecord, Pattern)
from app.execution.models import Outcome
from app.execution_engine.models import Execution, ExecutionLog as ExecEngineLog
from app.execution_log.models import ExecutionLog as ActExecLog
from app.communication.models import (
    CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope,
    ExternalConversation, ExternalMessage, ExternalParticipant,
    ExternalAttachmentReference, SyncCursor, OAuthState,
    Message, MessageProposal,
)
from app.communication.inbound import InboundEvent
from app.human_context.models import ContextConcept, HumanContextItem, ContextProposal
from app.memory.models import MemoryConcept, MemoryCandidate, MemoryRecord, MemoryProvenance
from app.document.models import (
    DocumentRecord, DocumentSection, ExtractedField,
    DocumentComparison, ComparisonItem,
)
from app.llm.models import ModelRun
from app.shunya.knowledge_store import KnowledgeFact
from app.shunya.observer_learning import Observation as ShunyaObservation, LearningEntry
from app.privacy.models import (
    PrivacyPolicy, SensitivityPolicy, RetentionPolicy,
    MemoryEligibilityPolicy, SensitivityAssessment,
    PrivacyDecision, Restriction, ForgetRequest, PrivacyReviewItem,
)
from app.production.identity.workspace_model import Workspace as ProdWorkspace
from app.production.identity_repository import SHUNYAIdentityModel
from app.founder.models import (
    FounderSpace, FounderObject, FounderConversation,
    FounderMessage, BusinessRelationship,
)
from app.founder.workspace_models import (
    MissingContext, NextAction, WorkspaceEvent,
    WorkspaceHealthSnapshot, WorkspaceNavigation,
)
from app.genesis_protection import AuditLog as GenesisAuditLog
from app.intake.models import IntakeSignal
from app.objects.models import Object
from app.objects.legacy_models import Workspace as LegacyWorkspace, ShunyaObject
from app.signals.models import Signal
from app.graph.models import ObjectRelation
from app.commitments.models import Commitment
from app.observations.models import Observation
from app.core.entity import Entity
from app.customers.models import Customer
from app.finance.models import (
    Account, LedgerEntry, JournalEntry,
    FinInvoice as Invoice, InvoiceItem, FinancePayment as Payment,
    TaxProfile, PurchaseOrder, Budget,
)
from app.finance.controls import ApprovalRequest, ApprovalAction, Delegation, FinancialPeriod
from app.finance.evidence import FinancialEvidence, EvidencePolicy
from app.integration.models import (
    ContentGeneration, CachedMedia, CachedEmail,
    Notification as M6Notification, NotificationPreference, IntegrationConfig,
    IntegrationConnection, SocialAccount, ScheduledPost, AdCampaign,
)
from app.platform.models import WebhookSubscription, WebhookDelivery
from app.enterprise.models import (AuditRecord, EnterpriseRole, EnterpriseTeamMember)
from app.media import MediaFile
from app.relationship.models import (
    CanonicalRelationship, RelationshipCategory, RelationshipField,
    TimelineEntry, RelationshipMemory, RelationshipDocument,
    DuplicateGroup, DuplicateCandidate,
)
from app.marketing.models import Campaign, AudienceDefinition, CampaignContent, Experiment
from app.dynamic_fields import DynamicField, DynamicFieldValue
from app.workspace.models import WorkspacePolicy
from app.intelligence.models import Pattern as IntelPattern
from app.objects.legacy_models import ShunyaObject

# ===== Generate migration =====
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

tables = list(db.metadata.tables.items())
tables.sort(key=lambda x: x[0])

print("Tables:", file=sys.stderr)
for name, _ in tables:
    print(f"  {name}", file=sys.stderr)
print(f"\nTotal: {len(tables)}", file=sys.stderr)

dialect = postgresql.dialect()

lines = []
lines.append('"""Safe model-schema reconciliation: CREATE TABLE IF NOT EXISTS for all model tables.')
lines.append('')
lines.append(f'EMITS {len(tables)} tables. Uses IF NOT EXISTS — safe on any environment.')
lines.append('Generated from SQLAlchemy metadata after importing all models.')
lines.append('"""')
lines.append('')
lines.append('from alembic import op')
lines.append('import sqlalchemy as sa')
lines.append('from sqlalchemy.dialects import postgresql')
lines.append('')
lines.append('revision = "0010_safe_model_schema_reconciliation"')
lines.append('down_revision = "0009_org_scoped_workspaces"')
lines.append('branch_labels = None')
lines.append('depends_on = None')
lines.append('')
lines.append('')
lines.append('def upgrade():')
lines.append('    """Create all model tables with IF NOT EXISTS (idempotent)."""')
lines.append('')

for table_name, table in tables:
    ddl = str(CreateTable(table).compile(dialect=dialect))
    ddl = ddl.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", 1)
    lines.append(f'    op.execute(\'\'\'{ddl}\'\'\')')
    lines.append('')

lines.append('')
lines.append('def downgrade():')
lines.append('    """No-op: we cannot safely drop tables here.')
lines.append('    Individual migrations handle downgrade for their tables.')
lines.append('    """')
lines.append('    pass')
lines.append('')

migration_content = "\n".join(lines)

output_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "migrations", "versions",
    "0010_safe_model_schema_reconciliation.py"
)
with open(output_path, "w") as f:
    f.write(migration_content)

print(f"\nWritten: {output_path}", file=sys.stderr)
for name, _ in tables:
    print(name)