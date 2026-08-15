from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app import db
# Register ALL model modules so autogenerate captures the complete schema
from app.models import (  # noqa: F401
    Lead, Supplier, InvoiceStatus, TaskList, Task, Organization, Person, Document,
    OrgMember, OrgInvitation, Department,
)
from app.tenant import Tenant  # noqa: F401
from app.auth import TeamMember  # noqa: F401
from app.authz.models import Role, OrgMemberRole  # noqa: F401
from app.authz.extended_models import ServiceAccount, ApprovalDelegation, TenantPolicy  # noqa: F401
from app.evidence.models_db import EvidenceRecord  # noqa: F401
from app.evidence.decision_trace import DecisionTrace  # noqa: F401
from app.automation.models import AutomationRule  # noqa: F401
from app.intelligence.memory_store import LearningWeight  # noqa: F401
from app.execution.models import Outcome  # noqa: F401
from app.communication.models import (  # noqa: F401
    ExternalConversation, ExternalMessage, ExternalAttachmentReference,
    MessageProposal, ExternalParticipant, CommunicationSource,
    CommunicationCapturePolicy, CommunicationCaptureScope, SyncCursor, Message,
)
from app.communication.inbound import InboundEvent  # noqa: F401
from app.human_context.models import ContextConcept, HumanContextItem, ContextProposal  # noqa: F401
from app.memory.models import MemoryRecord, MemoryCandidate, MemoryProvenance, MemoryConcept  # noqa: F401
from app.document.models import (  # noqa: F401
    DocumentRecord, DocumentSection, ExtractedField, DocumentComparison, ComparisonItem,
)
from app.llm.models import ModelRun  # noqa: F401
from app.shunya.knowledge_store import KnowledgeFact  # noqa: F401
from app.privacy.models import MemoryEligibilityPolicy  # noqa: F401
from app.production.identity.workspace_model import Workspace  # noqa: F401
from app.production.identity_repository import SHUNYAIdentityModel  # noqa: F401
from app.founder.models import (  # noqa: F401
    FounderSpace, FounderObject, FounderConversation, FounderMessage, BusinessRelationship,
)
from app.genesis_protection import AuditLog  # noqa: F401
from app.security.audit import AuditLog as SecurityAuditLog  # noqa: F401
from app.intake.models import IntakeSignal  # noqa: F401
from app.objects.models import Object  # noqa: F401
from app.execution_engine.models import Execution  # noqa: F401
from app.intelligence.models import Pattern  # noqa: F401
from app.signals.models import Signal  # noqa: F401
from app.graph.models import ObjectRelation  # noqa: F401
from app.commitments.models import Commitment  # noqa: F401
from app.observations.models import Observation  # noqa: F401
from app.core.entity import Entity  # noqa: F401
from app.customers.models import Customer  # noqa: F401
from app.finance.models import (  # noqa: F401
    Account, LedgerEntry, JournalEntry,
    FinInvoice as Invoice, InvoiceItem, FinancePayment as Payment,
    TaxProfile, PurchaseOrder, Budget,
)
from app.finance.controls import ApprovalRequest, ApprovalAction, Delegation, FinancialPeriod  # noqa: F401
from app.finance.evidence import FinancialEvidence, EvidencePolicy  # noqa: F401
from app.objects.legacy_models import Workspace as LegacyWS, ShunyaObject  # noqa: F401
from app.integration.models import (  # noqa: F401
    ContentGeneration, CachedMedia, CachedEmail,
    Notification, NotificationPreference, IntegrationConfig,
    IntegrationConnection, SocialAccount, ScheduledPost, AdCampaign,
)
from app.founder.workspace_models import (  # noqa: F401
    MissingContext, NextAction, WorkspaceEvent, WorkspaceHealthSnapshot,
    WorkspaceNavigation,
)
target_metadata = db.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    # Read DATABASE_URL from environment, fall back to alembic.ini
    db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    config_section = config.get_section(config.config_ini_section)
    config_section["sqlalchemy.url"] = db_url
    connectable = engine_from_config(config_section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
