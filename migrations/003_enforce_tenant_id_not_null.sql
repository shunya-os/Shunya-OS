-- =============================================================================
-- Migration: Enforce NOT NULL on tenant_id columns
-- SHUNYA OS — Tenant Isolation Phase 2
-- Date: 2026-08-29
-- =============================================================================
-- 
-- This migration adds NOT NULL constraints to all tenant_id columns that are
-- currently nullable but have no NULL values in the database.
-- 
-- Pre-flight checks (run before migrating):
--   Confirm 0 NULLs with: SELECT COUNT(*) FROM <table> WHERE tenant_id IS NULL;
--
-- Rollback (if needed):
--   ALTER TABLE <table> ALTER COLUMN tenant_id DROP NOT NULL;
-- =============================================================================

BEGIN;

-- -------------------------------------------------------------------------
-- 1. Already NOT NULL (verified) — these tables already have the constraint
-- -------------------------------------------------------------------------
-- ✓ team_members: nullable=False, 0/5 NULL
-- ✓ documents:    nullable=False, 0/15 NULL
-- ✓ leads:        nullable=False, 0/6 NULL
-- ✓ campaigns:    nullable=False, 0/5 NULL
-- (No action needed for these)

-- -------------------------------------------------------------------------
-- 2. Tables with data and 0 NULLs — safe to add NOT NULL
-- -------------------------------------------------------------------------
ALTER TABLE commitments ALTER COLUMN tenant_id SET NOT NULL;

ALTER TABLE evidence_records ALTER COLUMN tenant_id SET NOT NULL;

-- -------------------------------------------------------------------------
-- 3. Empty tables — safe to add NOT NULL (no data to validate)
-- -------------------------------------------------------------------------
ALTER TABLE act_execution_logs ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE client_user_profiles ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE communication_capture_policies ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE communication_capture_scopes ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE communication_sources ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE comparison_items ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE context_proposals ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE customer ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE customer_profiles ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE document_comparisons ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE document_records ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE document_sections ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE employee_profiles ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE external_conversations ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE external_messages ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE external_participants ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE extracted_fields ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE forget_requests ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE human_context_items ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE intake_sessions ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE job_records ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE login_codes ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE memory_candidates ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE memory_eligibility_policies ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE memory_provenances ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE memory_records ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE messages ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE model_runs ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE oauth_states ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE privacy_decisions ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE privacy_policies ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE privacy_review_items ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE relationship_commitments ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE restrictions ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE retention_policies ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE sensitivity_assessments ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE sensitivity_policies ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE supplier_contact_profiles ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE sync_cursors ALTER COLUMN tenant_id SET NOT NULL;

COMMIT;

-- =============================================================================
-- Post-migration verification
-- =============================================================================
-- Run these queries to verify:
--
-- SELECT column_name, is_nullable
-- FROM information_schema.columns
-- WHERE column_name = 'tenant_id'
-- ORDER BY table_name;
--
-- Expected: is_nullable = 'NO' for all rows
-- =============================================================================