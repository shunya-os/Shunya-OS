"""Safe model-schema reconciliation: CREATE TABLE IF NOT EXISTS for all model tables.

EMITS 151 tables. Uses IF NOT EXISTS — safe on any environment.
Generated from SQLAlchemy metadata after importing all models.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_schema_reconciliation"
down_revision = "0009_org_scoped_workspaces"
branch_labels = None
depends_on = None


def upgrade():
    """Create all model tables with IF NOT EXISTS (idempotent)."""
    # FK constraints handled by model definitions / db.create_all()
    # This migration creates tables only; FK constraints are added
    # by the model-level metadata when the application first starts.

    op.execute('''
CREATE TABLE IF NOT EXISTS act_execution_logs (
	id SERIAL NOT NULL, 
	object_id INTEGER NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	event_type VARCHAR(50) NOT NULL, 
	payload JSON, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS activity_logs (
	id SERIAL NOT NULL, 
	lead_id INTEGER NOT NULL, 
	action VARCHAR(60) NOT NULL, 
	detail TEXT, 
	"user" VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS audience_definitions (
	id SERIAL NOT NULL, 
	campaign_id INTEGER, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	criteria_json TEXT, 
	source VARCHAR(60), 
	tenant_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS auth_delegations (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	delegator_id INTEGER NOT NULL, 
	delegate_id INTEGER NOT NULL, 
	permission_keys TEXT, 
	scope VARCHAR(30), 
	scope_id INTEGER, 
	reason TEXT, 
	status VARCHAR(20), 
	valid_from TIMESTAMP WITHOUT TIME ZONE, 
	valid_until TIMESTAMP WITHOUT TIME ZONE, 
	revoked_by VARCHAR(64), 
	revoked_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS auth_member_roles (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	member_id INTEGER NOT NULL, 
	role_id INTEGER NOT NULL, 
	scope VARCHAR(30), 
	scope_id INTEGER, 
	granted_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS auth_roles (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	display_name VARCHAR(255) NOT NULL, 
	description TEXT, 
	permissions TEXT, 
	is_system BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS auth_service_accounts (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	description TEXT, 
	token_hash VARCHAR(128) NOT NULL, 
	token_prefix VARCHAR(8) NOT NULL, 
	permissions TEXT, 
	allowed_scopes TEXT, 
	is_active BOOLEAN, 
	last_used_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS auth_tenant_policies (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	policy_key VARCHAR(120) NOT NULL, 
	policy_value TEXT NOT NULL, 
	policy_type VARCHAR(30), 
	description TEXT, 
	is_active BOOLEAN, 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS campaign_contents (
	id SERIAL NOT NULL, 
	campaign_id INTEGER NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	content_type VARCHAR(60), 
	body TEXT, 
	status VARCHAR(30), 
	asset_url VARCHAR(500), 
	owner VARCHAR(120), 
	approval_commitment_id INTEGER, 
	tenant_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS campaigns (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	objective VARCHAR(80), 
	owner VARCHAR(120), 
	status VARCHAR(30), 
	budget NUMERIC(12, 2), 
	budget_type VARCHAR(20), 
	start_date TIMESTAMP WITHOUT TIME ZONE, 
	end_date TIMESTAMP WITHOUT TIME ZONE, 
	utm_source VARCHAR(255), 
	utm_campaign VARCHAR(255), 
	utm_medium VARCHAR(255), 
	tenant_id INTEGER NOT NULL, 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS celebrations (
	id SERIAL NOT NULL, 
	type VARCHAR(30) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	message TEXT, 
	icon VARCHAR(20), 
	animation VARCHAR(30), 
	lead_id INTEGER, 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS commitment_observations (
	id SERIAL NOT NULL, 
	commitment_id INTEGER NOT NULL, 
	entity_id INTEGER, 
	observed_value JSON NOT NULL, 
	expected_value JSON, 
	context JSON, 
	status VARCHAR(50), 
	recorded_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS commitments (
	id SERIAL NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	owner VARCHAR(100), 
	due_at TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(50), 
	relationship_id INTEGER, 
	campaign_id INTEGER, 
	issue_type VARCHAR(60), 
	meta JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS communication_capture_policies (
	id SERIAL NOT NULL, 
	source_id INTEGER NOT NULL, 
	tenant_id INTEGER, 
	account_mode VARCHAR(30) NOT NULL, 
	default_chat_policy VARCHAR(30), 
	default_group_policy VARCHAR(30), 
	unknown_contact_policy VARCHAR(30), 
	media_policy VARCHAR(30), 
	historical_sync_boundary TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS communication_capture_scopes (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	source_id INTEGER NOT NULL, 
	external_chat_id VARCHAR(255) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	approved_by VARCHAR(120), 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	reason TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS communication_sources (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	provider VARCHAR(60) NOT NULL, 
	account_identifier VARCHAR(255) NOT NULL, 
	account_mode VARCHAR(30) NOT NULL, 
	credential_reference VARCHAR(255), 
	capabilities_json TEXT, 
	metadata_json TEXT, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS comparison_items (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	comparison_id INTEGER NOT NULL, 
	field_key VARCHAR(255) NOT NULL, 
	left_value TEXT, 
	right_value TEXT, 
	result VARCHAR(30) NOT NULL, 
	location_left VARCHAR(200), 
	location_right VARCHAR(200), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS context_concepts (
	id SERIAL NOT NULL, 
	context_key VARCHAR(255) NOT NULL, 
	value_type VARCHAR(30) NOT NULL, 
	allowed_scope_types TEXT, 
	allowed_values TEXT, 
	sensitivity_expectation VARCHAR(30), 
	global_promotion_eligible BOOLEAN, 
	description TEXT, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (context_key)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS context_proposals (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	person_id INTEGER NOT NULL, 
	relationship_id INTEGER, 
	context_category VARCHAR(60) NOT NULL, 
	context_key VARCHAR(255) NOT NULL, 
	value TEXT NOT NULL, 
	value_type VARCHAR(30), 
	summary VARCHAR(500), 
	scope_type VARCHAR(30) NOT NULL, 
	source_object_type VARCHAR(60), 
	source_object_id INTEGER, 
	assertion_type VARCHAR(30) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	approved_by VARCHAR(120), 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	policy_version_at_approval INTEGER, 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS customer (
	id SERIAL NOT NULL, 
	name VARCHAR(120), 
	phone VARCHAR(20), 
	email VARCHAR(120), 
	relationship_id INTEGER, 
	lead_id INTEGER, 
	tenant_id INTEGER, 
	status VARCHAR(30), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS decision_traces (
	id SERIAL NOT NULL, 
	object_id INTEGER, 
	main_decision JSON, 
	shadow_outputs JSON, 
	comparison_result JSON, 
	final_decision JSON, 
	source VARCHAR(50), 
	confidence FLOAT, 
	shadow_agreement_pct FLOAT, 
	execution_status VARCHAR(20), 
	execution_output JSON, 
	error_message TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS departments (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	head_identity_id VARCHAR(64), 
	parent_department_id INTEGER, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS document_comparisons (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	left_document_id INTEGER NOT NULL, 
	right_document_id INTEGER NOT NULL, 
	comparison_state VARCHAR(30), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS document_records (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	source_reference_id INTEGER, 
	original_filename VARCHAR(500), 
	safe_display_name VARCHAR(500), 
	mime_type VARCHAR(100), 
	content_hash VARCHAR(128), 
	file_size INTEGER, 
	page_count INTEGER, 
	sheet_count INTEGER, 
	slide_count INTEGER, 
	classification VARCHAR(60), 
	lifecycle VARCHAR(30) NOT NULL, 
	ingestion_mechanism VARCHAR(30), 
	ocr_state VARCHAR(50), 
	parser_mechanism VARCHAR(60), 
	parser_version VARCHAR(30), 
	storage_reference VARCHAR(500), 
	supersedes_id INTEGER, 
	superseded_by_id INTEGER, 
	privacy_decision_id INTEGER, 
	observed_at TIMESTAMP WITHOUT TIME ZONE, 
	actor VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS document_sections (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	document_id INTEGER NOT NULL, 
	section_type VARCHAR(30), 
	page_number INTEGER, 
	sheet_name VARCHAR(200), 
	slide_number INTEGER, 
	block_order INTEGER, 
	heading VARCHAR(500), 
	content_preview VARCHAR(500), 
	content_hash VARCHAR(64), 
	parser_mechanism VARCHAR(60), 
	status VARCHAR(30), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS documents (
	id SERIAL NOT NULL, 
	lead_id INTEGER, 
	filename VARCHAR(500) NOT NULL, 
	file_path VARCHAR(1000) NOT NULL, 
	file_type VARCHAR(20) NOT NULL, 
	extracted_text TEXT, 
	structured_data TEXT, 
	classification VARCHAR(50), 
	uploaded_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS dynamic_field_values (
	id SERIAL NOT NULL, 
	field_id INTEGER NOT NULL, 
	entity_id INTEGER NOT NULL, 
	value TEXT, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS dynamic_fields (
	id SERIAL NOT NULL, 
	entity VARCHAR(60) NOT NULL, 
	field_name VARCHAR(120) NOT NULL, 
	field_label VARCHAR(120) NOT NULL, 
	field_type VARCHAR(30), 
	options TEXT, 
	is_required BOOLEAN, 
	placeholder VARCHAR(255), 
	help_text VARCHAR(500), 
	show_in_form BOOLEAN, 
	show_in_detail BOOLEAN, 
	searchable BOOLEAN, 
	sort_order INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS email_verification_tokens (
	id SERIAL NOT NULL, 
	token VARCHAR(128) NOT NULL, 
	user_id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	verified BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS entities (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	definition_id INTEGER NOT NULL, 
	code VARCHAR(100), 
	status VARCHAR(50), 
	assigned_to INTEGER, 
	data JSON, 
	ai_summary TEXT, 
	tags JSON, 
	is_archived BOOLEAN, 
	created_by INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	code_prefix VARCHAR(20), 
	type VARCHAR(50), 
	state VARCHAR(50), 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS evidence_records (
	id SERIAL NOT NULL, 
	source_type VARCHAR(50) NOT NULL, 
	source_id VARCHAR(100) NOT NULL, 
	raw_reference JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_evidence_source UNIQUE (source_type, source_id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS execution_logs (
	id SERIAL NOT NULL, 
	object_id INTEGER NOT NULL, 
	action_type VARCHAR(255) NOT NULL, 
	payload JSON, 
	state_before JSON, 
	state_after JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS executions (
	id SERIAL NOT NULL, 
	object_id INTEGER NOT NULL, 
	decision VARCHAR(255), 
	status VARCHAR(50), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS experiments (
	id SERIAL NOT NULL, 
	campaign_id INTEGER, 
	name VARCHAR(255) NOT NULL, 
	hypothesis TEXT, 
	variant VARCHAR(60), 
	status VARCHAR(30), 
	metric VARCHAR(60), 
	confidence FLOAT, 
	sample_size INTEGER, 
	tenant_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS external_attachment_references (
	id SERIAL NOT NULL, 
	message_id INTEGER NOT NULL, 
	provider_media_id VARCHAR(255), 
	mime_type VARCHAR(120), 
	filename VARCHAR(500), 
	size_bytes BIGINT, 
	routing_status VARCHAR(30), 
	provider_metadata TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS external_conversations (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	source_id INTEGER NOT NULL, 
	provider_chat_id VARCHAR(255) NOT NULL, 
	conversation_type VARCHAR(30), 
	subject VARCHAR(500), 
	message_count INTEGER, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	latest_message_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS external_messages (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	source_id INTEGER NOT NULL, 
	conversation_id INTEGER NOT NULL, 
	provider_message_id VARCHAR(255) NOT NULL, 
	sender_participant_id INTEGER, 
	body TEXT, 
	capture_status VARCHAR(30), 
	message_type VARCHAR(30), 
	direction VARCHAR(10), 
	provider_thread_id VARCHAR(255), 
	original_timestamp TIMESTAMP WITHOUT TIME ZONE, 
	received_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS external_participants (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	source_id INTEGER NOT NULL, 
	provider_participant_id VARCHAR(255) NOT NULL, 
	display_name VARCHAR(255), 
	raw_identifier VARCHAR(255), 
	person_id INTEGER, 
	identity_resolution_status VARCHAR(30), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS extracted_fields (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	document_id INTEGER NOT NULL, 
	section_id INTEGER, 
	field_key VARCHAR(255) NOT NULL, 
	value TEXT NOT NULL, 
	value_type VARCHAR(30), 
	location VARCHAR(200), 
	extraction_mechanism VARCHAR(60), 
	extraction_status VARCHAR(30), 
	status VARCHAR(30), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_accounts (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	code VARCHAR(30) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	type VARCHAR(30) NOT NULL, 
	subtype VARCHAR(60), 
	is_active BOOLEAN, 
	is_control BOOLEAN, 
	parent_id INTEGER, 
	currency VARCHAR(10), 
	description TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_approval_actions (
	id SERIAL NOT NULL, 
	approval_request_id INTEGER NOT NULL, 
	organization_id INTEGER NOT NULL, 
	level INTEGER NOT NULL, 
	action VARCHAR(30) NOT NULL, 
	actor VARCHAR(64) NOT NULL, 
	note TEXT, 
	acted_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_approval_requests (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	doc_type VARCHAR(60) NOT NULL, 
	doc_id INTEGER NOT NULL, 
	policy_id VARCHAR(60) NOT NULL, 
	amount NUMERIC(15, 2), 
	status VARCHAR(30), 
	requested_by VARCHAR(64) NOT NULL, 
	requested_at TIMESTAMP WITHOUT TIME ZONE, 
	reason TEXT, 
	current_level INTEGER, 
	levels INTEGER, 
	escalated BOOLEAN, 
	resolved_by VARCHAR(64), 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	resolution VARCHAR(30), 
	resolution_note TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_budgets (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	fiscal_year INTEGER NOT NULL, 
	period VARCHAR(30), 
	amount NUMERIC(15, 2), 
	spent_amount NUMERIC(15, 2), 
	account_id INTEGER, 
	department_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_delegations (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	delegator_id VARCHAR(64) NOT NULL, 
	delegate_id VARCHAR(64) NOT NULL, 
	role VARCHAR(120) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	scope VARCHAR(60), 
	max_amount NUMERIC(15, 2), 
	is_active BOOLEAN, 
	revoked_at TIMESTAMP WITHOUT TIME ZONE, 
	revoked_by VARCHAR(64), 
	reason TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_evidence (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	reference_type VARCHAR(60) NOT NULL, 
	reference_id INTEGER NOT NULL, 
	evidence_type VARCHAR(30), 
	file_path VARCHAR(500), 
	original_filename VARCHAR(500), 
	mime_type VARCHAR(100), 
	file_size_bytes BIGINT, 
	status VARCHAR(30), 
	notes TEXT, 
	extracted_data TEXT, 
	matched_reference VARCHAR(60), 
	matched_id INTEGER, 
	verified_by VARCHAR(64), 
	verified_at TIMESTAMP WITHOUT TIME ZONE, 
	rejected_reason TEXT, 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_evidence_policies (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	doc_type VARCHAR(60) NOT NULL, 
	requirement VARCHAR(30), 
	condition TEXT, 
	min_count INTEGER, 
	allowed_types TEXT, 
	require_ocr BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_invoice_items (
	id SERIAL NOT NULL, 
	invoice_id INTEGER NOT NULL, 
	description VARCHAR(500) NOT NULL, 
	quantity NUMERIC(12, 2), 
	unit_price NUMERIC(15, 2), 
	tax_rate NUMERIC(5, 2), 
	tax_amount NUMERIC(15, 2), 
	discount_amount NUMERIC(15, 2), 
	total_amount NUMERIC(15, 2), 
	account_id INTEGER, 
	sort_order INTEGER, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_invoices (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	relationship_id INTEGER, 
	proposal_id INTEGER, 
	number VARCHAR(60) NOT NULL, 
	type VARCHAR(30), 
	status VARCHAR(30), 
	issue_date DATE NOT NULL, 
	due_date DATE, 
	currency VARCHAR(10), 
	subtotal NUMERIC(15, 2), 
	tax_amount NUMERIC(15, 2), 
	discount_amount NUMERIC(15, 2), 
	total_amount NUMERIC(15, 2), 
	paid_amount NUMERIC(15, 2), 
	notes TEXT, 
	terms TEXT, 
	journal_entry_id INTEGER, 
	created_by VARCHAR(64), 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	paid_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_journal_entries (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	entry_date DATE NOT NULL, 
	number VARCHAR(60), 
	type VARCHAR(30), 
	status VARCHAR(30), 
	description TEXT, 
	reference_type VARCHAR(60), 
	reference_id INTEGER, 
	created_by VARCHAR(64), 
	posted_at TIMESTAMP WITHOUT TIME ZONE, 
	reversed_by VARCHAR(64), 
	reversed_at TIMESTAMP WITHOUT TIME ZONE, 
	reversal_of INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_ledger (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	account_id INTEGER NOT NULL, 
	journal_entry_id INTEGER NOT NULL, 
	entry_date DATE NOT NULL, 
	debit NUMERIC(15, 2), 
	credit NUMERIC(15, 2), 
	reference_type VARCHAR(60), 
	reference_id INTEGER, 
	description TEXT, 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_payments (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	invoice_id INTEGER, 
	relationship_id INTEGER, 
	type VARCHAR(30), 
	amount NUMERIC(15, 2) NOT NULL, 
	currency VARCHAR(10), 
	payment_date DATE NOT NULL, 
	method VARCHAR(60), 
	reference_number VARCHAR(255), 
	notes TEXT, 
	journal_entry_id INTEGER, 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_periods (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	year INTEGER NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	status VARCHAR(30), 
	closed_by VARCHAR(64), 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	reopened_by VARCHAR(64), 
	reopened_at TIMESTAMP WITHOUT TIME ZONE, 
	reopen_reason TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_purchase_orders (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	relationship_id INTEGER, 
	number VARCHAR(60) NOT NULL, 
	status VARCHAR(30), 
	order_date DATE NOT NULL, 
	expected_date DATE, 
	currency VARCHAR(10), 
	total_amount NUMERIC(15, 2), 
	notes TEXT, 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS fin_tax_profiles (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	rate NUMERIC(5, 2) NOT NULL, 
	type VARCHAR(30), 
	is_active BOOLEAN, 
	account_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS forget_requests (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	person_id INTEGER, 
	request_type VARCHAR(60) NOT NULL, 
	subject_scope VARCHAR(255), 
	reason TEXT, 
	status VARCHAR(30) NOT NULL, 
	approved_by VARCHAR(120), 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS founder_conversations (
	id SERIAL NOT NULL, 
	conv_id VARCHAR(64) NOT NULL, 
	object_id VARCHAR(64) NOT NULL, 
	title VARCHAR(255), 
	identity_id VARCHAR(64) NOT NULL, 
	status VARCHAR(30), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS founder_messages (
	id SERIAL NOT NULL, 
	conv_id VARCHAR(64) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	content TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS founder_objects (
	id SERIAL NOT NULL, 
	object_id VARCHAR(64) NOT NULL, 
	space_id VARCHAR(64) NOT NULL, 
	object_type VARCHAR(60), 
	name VARCHAR(255) NOT NULL, 
	content TEXT, 
	status VARCHAR(30), 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS founder_relationships (
	id SERIAL NOT NULL, 
	rel_id VARCHAR(64) NOT NULL, 
	space_id VARCHAR(64) NOT NULL, 
	rel_type VARCHAR(30) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	email VARCHAR(255), 
	phone VARCHAR(60), 
	company VARCHAR(255), 
	notes TEXT, 
	tags VARCHAR(500), 
	status VARCHAR(30), 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS founder_spaces (
	id SERIAL NOT NULL, 
	space_id VARCHAR(64) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	space_type VARCHAR(30), 
	description TEXT, 
	identity_id VARCHAR(64) NOT NULL, 
	member_count INTEGER, 
	organization_id INTEGER, 
	status VARCHAR(30), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS genesis_audit_log (
	id SERIAL NOT NULL, 
	event_id VARCHAR(64) NOT NULL, 
	actor_id VARCHAR(128) NOT NULL, 
	actor_name VARCHAR(255), 
	entity_type VARCHAR(60) NOT NULL, 
	entity_id VARCHAR(128) NOT NULL, 
	entity_name VARCHAR(255), 
	operation VARCHAR(60) NOT NULL, 
	outcome VARCHAR(30) NOT NULL, 
	explanation TEXT, 
	details TEXT, 
	restoration_event_id VARCHAR(64), 
	restoration_status VARCHAR(30), 
	occurred_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (event_id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS human_context_items (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	person_id INTEGER NOT NULL, 
	relationship_id INTEGER, 
	context_category VARCHAR(60) NOT NULL, 
	context_key VARCHAR(255) NOT NULL, 
	value TEXT NOT NULL, 
	value_type VARCHAR(30), 
	summary VARCHAR(500), 
	scope_type VARCHAR(30) NOT NULL, 
	scope_object_type VARCHAR(60), 
	scope_object_id INTEGER, 
	valid_from TIMESTAMP WITHOUT TIME ZONE, 
	valid_until TIMESTAMP WITHOUT TIME ZONE, 
	observed_at TIMESTAMP WITHOUT TIME ZONE, 
	source_object_type VARCHAR(60), 
	source_object_id INTEGER, 
	assertion_type VARCHAR(30) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	supersedes_id INTEGER, 
	superseded_by_id INTEGER, 
	privacy_decision_id INTEGER, 
	memory_eligibility_state VARCHAR(30), 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS inbound_events (
	id SERIAL NOT NULL, 
	source VARCHAR(100), 
	payload JSON, 
	processed BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS intake_candidates (
	id SERIAL NOT NULL, 
	session_id INTEGER NOT NULL, 
	row_index INTEGER, 
	raw_data TEXT, 
	normalized_data TEXT, 
	classification VARCHAR(30), 
	identity_status VARCHAR(30), 
	matched_person_id INTEGER, 
	identity_conflict TEXT, 
	validation_status VARCHAR(30), 
	validation_messages TEXT, 
	duplicate_type VARCHAR(30), 
	duplicate_group VARCHAR(64), 
	import_status VARCHAR(30), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS intake_field_mappings (
	id SERIAL NOT NULL, 
	session_id INTEGER NOT NULL, 
	source_column VARCHAR(255) NOT NULL, 
	target_field VARCHAR(255), 
	target_domain VARCHAR(60), 
	mapping_status VARCHAR(30), 
	mapping_method VARCHAR(30), 
	confidence FLOAT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS intake_sessions (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	source_type VARCHAR(30) NOT NULL, 
	source_name VARCHAR(255), 
	source_checksum VARCHAR(64), 
	row_count INTEGER, 
	column_names TEXT, 
	status VARCHAR(30), 
	summary TEXT, 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	proposal_version INTEGER, 
	proposal_generated_at TIMESTAMP WITHOUT TIME ZONE, 
	approved_by VARCHAR(120), 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	approved_proposal_version INTEGER, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS intake_signals (
	id SERIAL NOT NULL, 
	raw_input TEXT NOT NULL, 
	input_type VARCHAR(50) NOT NULL, 
	structured_data JSON, 
	status VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS invitation_tokens (
	id SERIAL NOT NULL, 
	token VARCHAR(128) NOT NULL, 
	org_id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	role VARCHAR(30) NOT NULL, 
	name VARCHAR(255), 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	accepted_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS knowledge_documents (
	id SERIAL NOT NULL, 
	organization_id INTEGER, 
	title VARCHAR(500) NOT NULL, 
	category VARCHAR(60), 
	file_path VARCHAR(500), 
	file_type VARCHAR(60), 
	file_size_bytes BIGINT, 
	extracted_text TEXT, 
	summary TEXT, 
	tags VARCHAR(1000), 
	uploaded_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS knowledge_facts (
	id SERIAL NOT NULL, 
	fact_key VARCHAR(255) NOT NULL, 
	version INTEGER NOT NULL, 
	domain VARCHAR(60), 
	category VARCHAR(120), 
	value TEXT NOT NULL, 
	value_type VARCHAR(60), 
	confidence FLOAT, 
	evidence TEXT, 
	source VARCHAR(255), 
	checksum VARCHAR(64), 
	created_by VARCHAR(120), 
	superseded_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (checksum)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS leads (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	source VARCHAR(30), 
	customer_name VARCHAR(255), 
	phone VARCHAR(30), 
	email VARCHAR(255), 
	destination VARCHAR(255), 
	pax VARCHAR(100), 
	dates VARCHAR(255), 
	budget NUMERIC(12, 2), 
	notes TEXT, 
	status VARCHAR(30), 
	assigned_to VARCHAR(120), 
	entity_id INTEGER, 
	outcome VARCHAR(120), 
	stage VARCHAR(50), 
	person_id INTEGER, 
	tenant_id INTEGER, 
	campaign_id INTEGER, 
	utm_source VARCHAR(255), 
	utm_campaign VARCHAR(255), 
	utm_medium VARCHAR(255), 
	utm_term VARCHAR(255), 
	utm_content VARCHAR(255), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS learning_entries (
	id SERIAL NOT NULL, 
	observation_id INTEGER, 
	knowledge_fact_key VARCHAR(255), 
	insight TEXT NOT NULL, 
	recommendation TEXT, 
	source VARCHAR(60), 
	applied BOOLEAN, 
	applied_at TIMESTAMP WITHOUT TIME ZONE, 
	confidence FLOAT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS learning_weights (
	id SERIAL NOT NULL, 
	key VARCHAR(100) NOT NULL, 
	weight FLOAT, 
	sample_count INTEGER, 
	last_updated TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m6_ad_campaigns (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	platform VARCHAR(40) NOT NULL, 
	campaign_name VARCHAR(255) NOT NULL, 
	campaign_objective VARCHAR(80), 
	budget FLOAT, 
	budget_type VARCHAR(20), 
	start_date TIMESTAMP WITHOUT TIME ZONE, 
	end_date TIMESTAMP WITHOUT TIME ZONE, 
	targeting JSON, 
	creative JSON, 
	status VARCHAR(20), 
	external_campaign_id VARCHAR(255), 
	performance_metrics JSON, 
	error_message TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m6_cached_emails (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	message_id VARCHAR(255) NOT NULL, 
	thread_id VARCHAR(255), 
	from_email VARCHAR(255) NOT NULL, 
	from_name VARCHAR(255), 
	to_email TEXT, 
	subject VARCHAR(500), 
	body_preview VARCHAR(500), 
	body_text TEXT, 
	received_at TIMESTAMP WITHOUT TIME ZONE, 
	object_id VARCHAR(64), 
	is_processed BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m6_cached_media (
	id SERIAL NOT NULL, 
	provider VARCHAR(40) NOT NULL, 
	query_hash VARCHAR(64) NOT NULL, 
	query VARCHAR(500) NOT NULL, 
	response_data JSON, 
	total_count INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m6_content_generations (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	content_type VARCHAR(40) NOT NULL, 
	platform VARCHAR(40), 
	prompt TEXT NOT NULL, 
	generated_content TEXT, 
	tone VARCHAR(40), 
	target_audience VARCHAR(255), 
	word_count INTEGER, 
	ai_model VARCHAR(60), 
	is_favorited BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m6_integration_configs (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	provider VARCHAR(60) NOT NULL, 
	config_key VARCHAR(120) NOT NULL, 
	config_value TEXT, 
	config_json JSON, 
	is_active BOOLEAN, 
	label VARCHAR(255), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m6_integrations (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	provider VARCHAR(40) NOT NULL, 
	label VARCHAR(255), 
	access_token TEXT, 
	refresh_token TEXT, 
	token_expires_at TIMESTAMP WITHOUT TIME ZONE, 
	is_active BOOLEAN, 
	last_sync_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m6_notif_prefs (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	email_notifications BOOLEAN, 
	in_app_notifications BOOLEAN, 
	digest_frequency VARCHAR(20), 
	quiet_hours_start VARCHAR(5), 
	quiet_hours_end VARCHAR(5), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m6_notifications (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	notification_type VARCHAR(40) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	body TEXT, 
	object_id VARCHAR(64), 
	space_id VARCHAR(64), 
	conv_id VARCHAR(64), 
	is_read BOOLEAN NOT NULL, 
	is_email_sent BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	read_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m6_scheduled_posts (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	platform VARCHAR(40) NOT NULL, 
	content TEXT NOT NULL, 
	media_urls JSON, 
	scheduled_at TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(20), 
	published_at TIMESTAMP WITHOUT TIME ZONE, 
	post_url VARCHAR(500), 
	error_message TEXT, 
	engagement_metrics JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m6_social_accounts (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	platform VARCHAR(40) NOT NULL, 
	account_name VARCHAR(255) NOT NULL, 
	account_id VARCHAR(255), 
	access_token TEXT, 
	refresh_token TEXT, 
	token_expires_at TIMESTAMP WITHOUT TIME ZONE, 
	profile_picture_url VARCHAR(500), 
	profile_url VARCHAR(500), 
	follower_count INTEGER, 
	is_active BOOLEAN, 
	last_sync_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m7_automation_logs (
	id SERIAL NOT NULL, 
	rule_id INTEGER NOT NULL, 
	rule_name VARCHAR(255), 
	trigger_type VARCHAR(40), 
	trigger_object_id VARCHAR(64), 
	trigger_summary VARCHAR(500), 
	action_type VARCHAR(40), 
	action_summary VARCHAR(500), 
	status VARCHAR(20), 
	error_message TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m7_automation_rules (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	space_id VARCHAR(64), 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	trigger_type VARCHAR(40) NOT NULL, 
	trigger_config TEXT, 
	action_type VARCHAR(40) NOT NULL, 
	action_config TEXT, 
	is_active BOOLEAN NOT NULL, 
	execution_count INTEGER, 
	last_executed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m8_anomaly_records (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	object_id VARCHAR(64), 
	anomaly_type VARCHAR(40) NOT NULL, 
	severity VARCHAR(20), 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	evidence TEXT, 
	status VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m8_learning_events (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	learning_type VARCHAR(40) NOT NULL, 
	trace_id VARCHAR(64), 
	trigger_summary VARCHAR(500), 
	before_state TEXT, 
	after_state TEXT, 
	outcome VARCHAR(100), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m8_reasoning_traces (
	id SERIAL NOT NULL, 
	trace_id VARCHAR(64) NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	object_id VARCHAR(64), 
	reasoning_type VARCHAR(40) NOT NULL, 
	query_text TEXT, 
	context_summary VARCHAR(500), 
	reasoning_chain TEXT, 
	confidence_score FLOAT, 
	ai_response TEXT, 
	sources TEXT, 
	is_corrected BOOLEAN, 
	corrected_response TEXT, 
	execution_time_ms INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m9_audit_records (
	id SERIAL NOT NULL, 
	actor_id VARCHAR(64) NOT NULL, 
	actor_name VARCHAR(255), 
	action VARCHAR(40) NOT NULL, 
	entity_type VARCHAR(40) NOT NULL, 
	entity_id VARCHAR(64), 
	entity_name VARCHAR(255), 
	details TEXT, 
	ip_address VARCHAR(45), 
	organization_id VARCHAR(64), 
	recorded_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m9_roles (
	id SERIAL NOT NULL, 
	organization_id VARCHAR(64) NOT NULL, 
	name VARCHAR(60) NOT NULL, 
	description VARCHAR(255), 
	permissions TEXT, 
	is_system BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS m9_team_members (
	id SERIAL NOT NULL, 
	organization_id VARCHAR(64) NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	name VARCHAR(255), 
	email VARCHAR(255), 
	role_id INTEGER, 
	status VARCHAR(20), 
	invited_by VARCHAR(64), 
	joined_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_m9_org_member UNIQUE (organization_id, identity_id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS media_files (
	id SERIAL NOT NULL, 
	lead_id INTEGER, 
	filename VARCHAR(255) NOT NULL, 
	storage_path VARCHAR(500) NOT NULL, 
	file_type VARCHAR(60), 
	mime_type VARCHAR(120), 
	file_size INTEGER, 
	uploaded_by VARCHAR(120), 
	caption TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS memory_candidates (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	person_id INTEGER, 
	relationship_id INTEGER, 
	memory_type VARCHAR(60) NOT NULL, 
	memory_key VARCHAR(255) NOT NULL, 
	value TEXT NOT NULL, 
	value_type VARCHAR(30), 
	scope_type VARCHAR(30) NOT NULL, 
	scope_object_type VARCHAR(60), 
	scope_object_id INTEGER, 
	source_object_type VARCHAR(60), 
	source_object_id INTEGER, 
	human_context_item_id INTEGER, 
	creation_mechanism VARCHAR(30) NOT NULL, 
	truth_classification VARCHAR(20) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	approved_by VARCHAR(120), 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	policy_version_at_approval INTEGER, 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS memory_concepts (
	id SERIAL NOT NULL, 
	memory_key VARCHAR(255) NOT NULL, 
	memory_type VARCHAR(60) NOT NULL, 
	value_type VARCHAR(30) NOT NULL, 
	allowed_scopes TEXT, 
	sensitivity_expectation VARCHAR(30), 
	context_promotion_eligible BOOLEAN, 
	global_promotion_eligible BOOLEAN, 
	description TEXT, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (memory_key)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS memory_eligibility_policies (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	policy_version INTEGER, 
	source_type VARCHAR(60), 
	reason_code VARCHAR(60), 
	decision VARCHAR(30) NOT NULL, 
	is_system BOOLEAN, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS memory_provenances (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	memory_id INTEGER NOT NULL, 
	source_object_type VARCHAR(60) NOT NULL, 
	source_object_id INTEGER NOT NULL, 
	provenance_source VARCHAR(255), 
	provenance_source_id VARCHAR(255), 
	provenance_role VARCHAR(30), 
	observed_at TIMESTAMP WITHOUT TIME ZONE, 
	creation_mechanism VARCHAR(30), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_mp_source_idempotency UNIQUE (provenance_source, provenance_source_id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS memory_records (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	person_id INTEGER, 
	relationship_id INTEGER, 
	memory_type VARCHAR(60) NOT NULL, 
	memory_key VARCHAR(255) NOT NULL, 
	value TEXT NOT NULL, 
	value_type VARCHAR(30), 
	summary VARCHAR(500), 
	scope_type VARCHAR(30) NOT NULL, 
	scope_object_type VARCHAR(60), 
	scope_object_id INTEGER, 
	valid_from TIMESTAMP WITHOUT TIME ZONE, 
	valid_until TIMESTAMP WITHOUT TIME ZONE, 
	effective_from TIMESTAMP WITHOUT TIME ZONE, 
	effective_until TIMESTAMP WITHOUT TIME ZONE, 
	observed_at TIMESTAMP WITHOUT TIME ZONE, 
	source_object_type VARCHAR(60), 
	source_object_id INTEGER, 
	human_context_item_id INTEGER, 
	creation_mechanism VARCHAR(30) NOT NULL, 
	truth_classification VARCHAR(20) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	supersedes_id INTEGER, 
	superseded_by_id INTEGER, 
	resolution_type VARCHAR(30), 
	resolution_reason TEXT, 
	injection_checked BOOLEAN, 
	privacy_decision_id INTEGER, 
	memory_eligibility_state VARCHAR(30), 
	policy_version INTEGER, 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS message_proposals (
	id SERIAL NOT NULL, 
	"to" VARCHAR(64) NOT NULL, 
	message TEXT NOT NULL, 
	status VARCHAR(32), 
	approved_by VARCHAR(64), 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	edited_message TEXT, 
	entity_id INTEGER, 
	entity_type VARCHAR(64), 
	entity_name VARCHAR(128), 
	context_reason TEXT, 
	context_priority VARCHAR(16), 
	context_source VARCHAR(64), 
	context_confidence VARCHAR(16), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS messages (
	id SERIAL NOT NULL, 
	entity_id INTEGER NOT NULL, 
	direction VARCHAR(20), 
	channel VARCHAR(50), 
	content TEXT, 
	status VARCHAR(50), 
	metadata_json JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS model_runs (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	correlation_key VARCHAR(128), 
	purpose_code VARCHAR(60), 
	provider VARCHAR(60) NOT NULL, 
	provider_model_id VARCHAR(120), 
	canonical_model VARCHAR(60), 
	adapter_mechanism VARCHAR(60), 
	adapter_version VARCHAR(30), 
	status VARCHAR(30) NOT NULL, 
	finish_reason VARCHAR(60), 
	output_mode VARCHAR(30), 
	response_text TEXT, 
	structured_result TEXT, 
	tool_requests TEXT, 
	usage_prompt_tokens INTEGER, 
	usage_completion_tokens INTEGER, 
	usage_cost FLOAT, 
	error_class VARCHAR(60), 
	error_reason_code VARCHAR(60), 
	prompt_template_id VARCHAR(60), 
	prompt_template_version VARCHAR(30), 
	retry_count INTEGER, 
	parent_run_id INTEGER, 
	provider_reference_id VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS notifications (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	user_id INTEGER, 
	lead_id INTEGER, 
	type VARCHAR(30) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	message TEXT, 
	icon VARCHAR(50), 
	link VARCHAR(500), 
	is_read BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS oauth_states (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	provider VARCHAR(60) NOT NULL, 
	state VARCHAR(128) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (state)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS object_relations (
	id SERIAL NOT NULL, 
	source_object_id INTEGER NOT NULL, 
	target_object_id INTEGER NOT NULL, 
	relation_type VARCHAR(100), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS objects (
	id SERIAL NOT NULL, 
	object_type VARCHAR(100) NOT NULL, 
	state JSON, 
	context JSON, 
	tenant_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS observations (
	id SERIAL NOT NULL, 
	lead_id INTEGER, 
	action VARCHAR(60) NOT NULL, 
	expected_outcome TEXT, 
	actual_outcome TEXT, 
	discrepancy TEXT, 
	success BOOLEAN, 
	confidence FLOAT, 
	channel VARCHAR(30), 
	metadata_json TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS org_invitations (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	name VARCHAR(255), 
	role VARCHAR(30), 
	token VARCHAR(128) NOT NULL, 
	status VARCHAR(30), 
	invited_by VARCHAR(64), 
	accepted_at TIMESTAMP WITHOUT TIME ZONE, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (token)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS org_members (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	name VARCHAR(255), 
	email VARCHAR(255), 
	phone VARCHAR(60), 
	role VARCHAR(30), 
	designation VARCHAR(120), 
	department_id INTEGER, 
	is_active BOOLEAN, 
	joined_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	invited_by VARCHAR(64), 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS organizations (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(120) NOT NULL, 
	business_type VARCHAR(60), 
	logo_url VARCHAR(500), 
	brand_color VARCHAR(20), 
	brand_color_secondary VARCHAR(20), 
	brand_tagline VARCHAR(500), 
	brand_description TEXT, 
	tax_id VARCHAR(100), 
	registration_number VARCHAR(100), 
	phone VARCHAR(60), 
	email VARCHAR(255), 
	website VARCHAR(500), 
	address TEXT, 
	city VARCHAR(120), 
	state VARCHAR(120), 
	country VARCHAR(120), 
	postal_code VARCHAR(30), 
	timezone VARCHAR(60), 
	currency VARCHAR(10), 
	date_format VARCHAR(20), 
	is_active BOOLEAN, 
	max_members INTEGER, 
	ai_enabled BOOLEAN, 
	ai_config TEXT, 
	legacy_tenant_id INTEGER, 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (slug)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS password_reset_tokens (
	id SERIAL NOT NULL, 
	token VARCHAR(128) NOT NULL, 
	user_id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	used BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS patterns (
	id SERIAL NOT NULL, 
	object_type VARCHAR(100), 
	trigger_state JSON, 
	suggested_decision VARCHAR(255), 
	confidence FLOAT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS person_identities (
	id SERIAL NOT NULL, 
	person_id INTEGER, 
	identity_type VARCHAR(32) NOT NULL, 
	identity_value VARCHAR(255) NOT NULL, 
	normalized_value VARCHAR(255) NOT NULL, 
	source VARCHAR(60), 
	source_id VARCHAR(255), 
	confidence FLOAT, 
	metadata_json TEXT, 
	verification_state VARCHAR(32), 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS persons (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	name VARCHAR(255), 
	canonical_name VARCHAR(255) NOT NULL, 
	preferred_name VARCHAR(255), 
	identity_type VARCHAR(32), 
	metadata_json TEXT, 
	status VARCHAR(30), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS platform_webhook_deliveries (
	id SERIAL NOT NULL, 
	subscription_id INTEGER NOT NULL, 
	event_id VARCHAR(100) NOT NULL, 
	event_name VARCHAR(100) NOT NULL, 
	payload_json TEXT, 
	attempt INTEGER, 
	max_attempts INTEGER, 
	status VARCHAR(30), 
	http_status INTEGER, 
	response_body TEXT, 
	error TEXT, 
	next_retry_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	delivered_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_webhook_delivery_event UNIQUE (subscription_id, event_id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS platform_webhook_subscriptions (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(100) NOT NULL, 
	workspace_id VARCHAR(50), 
	label VARCHAR(200), 
	url VARCHAR(500) NOT NULL, 
	events_json TEXT, 
	secret VARCHAR(64) NOT NULL, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	last_delivery_at TIMESTAMP WITHOUT TIME ZONE, 
	last_delivery_status VARCHAR(30), 
	delivery_count INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_webhook_identity_url UNIQUE (identity_id, url)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS privacy_decisions (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	source_type VARCHAR(60) NOT NULL, 
	source_id INTEGER NOT NULL, 
	retention_decision VARCHAR(30), 
	retention_due_at TIMESTAMP WITHOUT TIME ZONE, 
	memory_eligibility VARCHAR(30) NOT NULL, 
	sensitivity_level VARCHAR(30), 
	policy_version INTEGER, 
	reason_codes TEXT, 
	evaluated_at TIMESTAMP WITHOUT TIME ZONE, 
	is_active BOOLEAN, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS privacy_policies (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	policy_version INTEGER, 
	default_sensitivity VARCHAR(30), 
	default_retention VARCHAR(30), 
	default_memory_eligibility VARCHAR(30), 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS privacy_review_items (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	source_type VARCHAR(60) NOT NULL, 
	source_id INTEGER NOT NULL, 
	reason_code VARCHAR(60), 
	decision_type VARCHAR(30) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	reviewed_by VARCHAR(120), 
	reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
	review_note TEXT, 
	policy_version INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS proposal_versions (
	id SERIAL NOT NULL, 
	proposal_id INTEGER NOT NULL, 
	version_number INTEGER NOT NULL, 
	snapshot_json TEXT, 
	change_summary VARCHAR(500), 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS proposals (
	id SERIAL NOT NULL, 
	organization_id INTEGER, 
	relationship_id INTEGER, 
	opportunity_id INTEGER, 
	version_number INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	title VARCHAR(500), 
	destination VARCHAR(255), 
	duration_days INTEGER, 
	pax VARCHAR(100), 
	budget NUMERIC(12, 2), 
	currency VARCHAR(10), 
	itinerary_json TEXT, 
	pricing_json TEXT, 
	inclusions TEXT, 
	exclusions TEXT, 
	terms TEXT, 
	brand_color VARCHAR(20), 
	brand_logo_url VARCHAR(500), 
	cover_image_url VARCHAR(500), 
	ai_generated BOOLEAN, 
	ai_model VARCHAR(100), 
	ai_prompt TEXT, 
	generation_notes TEXT, 
	web_html TEXT, 
	pdf_path VARCHAR(500), 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	sent_via VARCHAR(30), 
	viewed_at TIMESTAMP WITHOUT TIME ZONE, 
	accepted_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS rel_ai_memory (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	relationship_id INTEGER NOT NULL, 
	memory_json TEXT, 
	summary TEXT, 
	health_score INTEGER, 
	engagement_score INTEGER, 
	lifetime_value NUMERIC(15, 2), 
	retention_risk INTEGER, 
	last_ai_update TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (relationship_id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS rel_categories (
	id SERIAL NOT NULL, 
	organization_id INTEGER, 
	type_key VARCHAR(60) NOT NULL, 
	display_label VARCHAR(255) NOT NULL, 
	icon VARCHAR(60), 
	color VARCHAR(20), 
	is_system BOOLEAN, 
	sort_order INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS rel_custom_fields (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	field_key VARCHAR(120) NOT NULL, 
	field_label VARCHAR(255) NOT NULL, 
	field_type VARCHAR(30), 
	field_options TEXT, 
	is_required BOOLEAN, 
	sort_order INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS rel_documents (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	relationship_id INTEGER NOT NULL, 
	title VARCHAR(500) NOT NULL, 
	category VARCHAR(60), 
	file_path VARCHAR(500), 
	file_type VARCHAR(60), 
	file_size_bytes BIGINT, 
	extracted_text TEXT, 
	uploaded_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS rel_duplicate_candidates (
	id SERIAL NOT NULL, 
	group_id INTEGER NOT NULL, 
	relationship_id INTEGER NOT NULL, 
	match_reason VARCHAR(255), 
	match_score INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS rel_duplicate_groups (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	primary_relationship_id INTEGER, 
	merge_status VARCHAR(30), 
	detection_method VARCHAR(60), 
	confidence INTEGER, 
	resolved_by VARCHAR(64), 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS rel_relationships (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	display_name VARCHAR(255) NOT NULL, 
	legal_name VARCHAR(255), 
	preferred_name VARCHAR(255), 
	relationship_type VARCHAR(60) NOT NULL, 
	is_organization BOOLEAN, 
	company_name VARCHAR(255), 
	designation VARCHAR(255), 
	email VARCHAR(255), 
	email2 VARCHAR(255), 
	email3 VARCHAR(255), 
	phone VARCHAR(60), 
	phone2 VARCHAR(60), 
	phone3 VARCHAR(60), 
	address_line1 VARCHAR(500), 
	address_line2 VARCHAR(500), 
	city VARCHAR(120), 
	state VARCHAR(120), 
	postal_code VARCHAR(30), 
	country VARCHAR(120), 
	website VARCHAR(500), 
	social_linkedin VARCHAR(500), 
	social_twitter VARCHAR(500), 
	social_instagram VARCHAR(500), 
	social_facebook VARCHAR(500), 
	timezone VARCHAR(60), 
	preferred_language VARCHAR(10), 
	preferred_currency VARCHAR(10), 
	tags TEXT, 
	segments TEXT, 
	industries TEXT, 
	source VARCHAR(255), 
	referral_info TEXT, 
	risk_level VARCHAR(30), 
	priority INTEGER, 
	internal_owner VARCHAR(64), 
	status VARCHAR(30), 
	notes TEXT, 
	custom_attributes TEXT, 
	legacy_person_id INTEGER, 
	legacy_relationship_id INTEGER, 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS rel_timeline (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	relationship_id INTEGER NOT NULL, 
	event_type VARCHAR(60) NOT NULL, 
	event_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	title VARCHAR(500), 
	description TEXT, 
	reference_type VARCHAR(60), 
	reference_id INTEGER, 
	campaign_id INTEGER, 
	source_event VARCHAR(255), 
	metadata_json TEXT, 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS restrictions (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	person_id INTEGER, 
	restriction_type VARCHAR(60) NOT NULL, 
	scope VARCHAR(255), 
	reason TEXT, 
	created_by VARCHAR(120), 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS retention_policies (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	policy_version INTEGER, 
	source_type VARCHAR(60), 
	decision VARCHAR(30) NOT NULL, 
	retention_days INTEGER, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS sensitivity_assessments (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	source_type VARCHAR(60) NOT NULL, 
	source_id INTEGER NOT NULL, 
	sensitivity_level VARCHAR(30) NOT NULL, 
	reason_code VARCHAR(60), 
	reason_tags TEXT, 
	policy_version INTEGER, 
	evaluated_at TIMESTAMP WITHOUT TIME ZONE, 
	evaluation_mechanism VARCHAR(60), 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS sensitivity_policies (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	policy_version INTEGER, 
	source_type VARCHAR(60), 
	sensitivity_level VARCHAR(30) NOT NULL, 
	reason_code VARCHAR(60), 
	is_system BOOLEAN, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS sh_audit_logs (
	id SERIAL NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	identity_id VARCHAR(64), 
	workspace_id VARCHAR(20), 
	action VARCHAR(50) NOT NULL, 
	resource_type VARCHAR(50) NOT NULL, 
	resource_id VARCHAR(50), 
	ip_address VARCHAR(50), 
	user_agent VARCHAR(500), 
	details JSON, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS sh_objects (
	id SERIAL NOT NULL, 
	object_id VARCHAR(36) NOT NULL, 
	workspace_id VARCHAR(20) NOT NULL, 
	object_type VARCHAR(50) NOT NULL, 
	name VARCHAR(500) NOT NULL, 
	status VARCHAR(30), 
	data JSON, 
	created_by VARCHAR(64) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	is_deleted BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (object_id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS sh_outcomes (
	id SERIAL NOT NULL, 
	outcome_id VARCHAR(12) NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	intention TEXT NOT NULL, 
	stage VARCHAR(20) NOT NULL, 
	progress VARCHAR(200) NOT NULL, 
	expected_completion_seconds INTEGER, 
	actual_completion_seconds INTEGER, 
	recovery_history JSON, 
	final_summary JSON, 
	steps JSON, 
	last_error TEXT, 
	error_count INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS sh_workspaces (
	id VARCHAR(20) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	workspace_type VARCHAR(20) NOT NULL, 
	icon VARCHAR(10), 
	color VARCHAR(10), 
	description VARCHAR(500), 
	created_by VARCHAR(64) NOT NULL, 
	organization_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(20), 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS shunya_identities (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	display_name VARCHAR(255) NOT NULL, 
	primary_email VARCHAR(255), 
	status VARCHAR(30), 
	auth_methods_json TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS signals (
	id SERIAL NOT NULL, 
	object_id INTEGER NOT NULL, 
	type VARCHAR(100) NOT NULL, 
	payload JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS suppliers (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	category VARCHAR(120), 
	contact VARCHAR(255), 
	email VARCHAR(255), 
	phone VARCHAR(30), 
	city VARCHAR(120), 
	gstin VARCHAR(50), 
	payment_terms VARCHAR(255), 
	notes TEXT, 
	rating INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS sync_cursors (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	source_id INTEGER NOT NULL, 
	sync_type VARCHAR(30) NOT NULL, 
	cursor_value TEXT, 
	cursor_state VARCHAR(30), 
	last_sync_at TIMESTAMP WITHOUT TIME ZONE, 
	message_count INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS task_lists (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	name VARCHAR(255) NOT NULL, 
	lead_id INTEGER, 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS tasks (
	id SERIAL NOT NULL, 
	lead_id INTEGER, 
	entity_id INTEGER, 
	task_list_id INTEGER NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	assigned_to VARCHAR(120), 
	priority VARCHAR(20), 
	status VARCHAR(30), 
	sort_order INTEGER, 
	due_date DATE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS team_members (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(30), 
	role VARCHAR(30), 
	password_hash VARCHAR(128), 
	api_token VARCHAR(128), 
	is_active BOOLEAN, 
	verified BOOLEAN, 
	verify_token VARCHAR(128), 
	onboarding_completed BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	last_login TIMESTAMP WITHOUT TIME ZONE, 
	person_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (api_token)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS tenant_themes (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	primary_color VARCHAR(30), 
	accent_color VARCHAR(30), 
	bg_color VARCHAR(30), 
	sidebar_bg VARCHAR(30), 
	font_family VARCHAR(60), 
	logo_path VARCHAR(500), 
	logo_style VARCHAR(30), 
	welcome_message TEXT, 
	company_motto VARCHAR(255), 
	custom_css TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS tenants (
	id SERIAL NOT NULL, 
	company_name VARCHAR(255) NOT NULL, 
	slug VARCHAR(120) NOT NULL, 
	business_type VARCHAR(60), 
	business_category VARCHAR(60), 
	company_email VARCHAR(255), 
	website VARCHAR(500), 
	phone VARCHAR(30), 
	industry VARCHAR(120), 
	country VARCHAR(60), 
	timezone VARCHAR(60), 
	currency VARCHAR(10), 
	preferences JSON, 
	parent_id INTEGER, 
	subdomain VARCHAR(120), 
	domain VARCHAR(255), 
	is_active BOOLEAN, 
	plan VARCHAR(30), 
	max_team_members INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (subdomain)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS wksp_events (
	id SERIAL NOT NULL, 
	object_id VARCHAR(64) NOT NULL, 
	event_type VARCHAR(40) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	detail TEXT, 
	provenance TEXT, 
	importance VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS wksp_health_snapshots (
	id SERIAL NOT NULL, 
	object_id VARCHAR(64) NOT NULL, 
	overall_score FLOAT NOT NULL, 
	completeness_score FLOAT, 
	activity_score FLOAT, 
	relationship_score FLOAT, 
	conversation_score FLOAT, 
	commitment_score FLOAT, 
	description TEXT, 
	breakdown TEXT, 
	recorded_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS wksp_missing_context (
	id SERIAL NOT NULL, 
	object_id VARCHAR(64) NOT NULL, 
	context_type VARCHAR(40) NOT NULL, 
	label VARCHAR(255) NOT NULL, 
	detail TEXT, 
	severity VARCHAR(20), 
	status VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS wksp_navigation (
	id SERIAL NOT NULL, 
	identity_id VARCHAR(64) NOT NULL, 
	source_object_id VARCHAR(64) NOT NULL, 
	target_object_id VARCHAR(64) NOT NULL, 
	relationship_type VARCHAR(40), 
	context_label VARCHAR(255), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS wksp_next_actions (
	id SERIAL NOT NULL, 
	object_id VARCHAR(64) NOT NULL, 
	action_type VARCHAR(40) NOT NULL, 
	label VARCHAR(255) NOT NULL, 
	explanation TEXT, 
	supporting_evidence TEXT, 
	priority VARCHAR(20), 
	priority_score FLOAT, 
	originating_runtime VARCHAR(60), 
	status VARCHAR(20), 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS wksp_policies (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	level VARCHAR(30) NOT NULL, 
	level_id INTEGER, 
	experience_key VARCHAR(60) NOT NULL, 
	setting VARCHAR(30) NOT NULL, 
	created_by VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_wksp_policy UNIQUE (organization_id, level, level_id, experience_key)
)

''')

    op.execute('''
CREATE TABLE IF NOT EXISTS workspaces (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(120) NOT NULL, 
	description TEXT, 
	settings TEXT, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

''')


def downgrade():
    """No-op: we cannot safely drop tables here.
    Individual migrations handle downgrade for their tables.
    """
    pass
