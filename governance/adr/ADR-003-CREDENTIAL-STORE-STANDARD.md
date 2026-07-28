# ADR-003: Credential Store Standard

**Class:** Engineering
**Status:** Proposed
**Date:** 2026-07-18
**Author:** Chief Software Architect
**Supersedes:** (none)
**Superseded by:** (none)

**Approval Authority:**
- If Engineering: Chief Software Architect
- If Architectural/Constitutional: Chief Constitutional Architect

---

## Context

### Problem

The Executor Engine (ES-005) specifies that credentials (API tokens, passwords, encryption keys, OAuth tokens) are resolved at execution time from a "credential store." However, no specification defines the credential store's interface, security model, integration with Phase 4 (Privacy), or operational characteristics. The credential store does not yet exist as an implementation.

Every engine specification includes a "Never access credentials" SHALL NEVER clause — all engines except the Executor are constitutionally prohibited from accessing credentials. The Executor resolves credentials only at execution time, never storing them in plans or passing them through event payloads.

### Current State

- **ES-005 (Executor Engine)** specifies:
  - Credentials are resolved by ID or alias at execution time
  - Credentials are passed to channel adapters for authentication
  - Credentials are discarded after the task completes
  - Credential resolution failure is isolated to that task
- **SHUNYA_SYSTEM_FLOW.md §12 (Secrets)** specifies:
  - Secrets are stored in a dedicated credential store
  - No engine stores secrets in its own data store
  - No engine passes secrets through event payloads
  - The Executor resolves secrets at delivery time, not at plan time
- **SHUNYA_SYSTEM_FLOW.md §12 (Privacy):** Phase 4 eligibility gates apply to all personal data — credentials are sensitive data that must pass through eligibility gates before release
- **No existing implementation** — search of the codebase for `credential_store` or `CredentialStore` returned zero results

### Constraints

- **Least Authority Principle (SHUNYA_ARCHITECTURE.md §6.3):** Packages only receive the information they require. Only the Executor Engine may resolve credentials.
- **No credential leakage (Constitutional):** Credentials must never appear in plans, event payloads, logs, or audit trails.
- **Phase 4 (Privacy) integration:** Credential release must pass through purpose-based eligibility gates before resolution.
- **Internal service, not engine:** The Credential Store is classified as Shared Infrastructure (SUPPORTING_ARCHITECTURE_JUSTIFICATION.md — Component 2). It does not require an Engine Specification.
- **No existing implementation:** The credential store is greenfield. Everything must be specified from scratch.

### Evidence

- ES-005 (Executor Engine) — Sections 1 (Execution Preparation: resolve credentials), 3 (Credential resolution flow), 4 (Credential contract), 8 (Failure: Credential store unavailable)
- SHUNYA_SYSTEM_FLOW.md — Section 12 (Secrets: dedicated credential store, no pass-through in events, resolved at delivery time)
- SHUNYA_ARCHITECTURE.md — Section 6.3 (Principle of Least Authority)
- SUPPORTING_ARCHITECTURE_JUSTIFICATION.md — Component 2 (Credential Store — Shared Infrastructure classification)
- ARCHITECTURE_BASELINE_REVIEW.md — M2: "Credential Store Interface Not Defined"
- ARCHITECTURE_FINDINGS_CLASSIFICATION.md — M2/R4/ADR-003: "Credential Store Interface Not Defined"

---

## Decision

Define the Credential Store as a shared infrastructure component with the following specification. The Credential Store is an **internal service of the Executor Engine (ES-005)** — it is defined as a dependency interface within ES-005's scope, not as an independent engine specification.

### Classification

**Shared Infrastructure** (per SUPPORTING_ARCHITECTURE_JUSTIFICATION.md — Component 2). The Credential Store:
- Is used exclusively by the Executor Engine for credential resolution
- Has no semantic lifecycle in the intelligence pipeline
- Does not compound intelligence
- Does not require independent governance (interface defined within ES-005)

### API Contract

```
interface CredentialStore:
  resolve(credential_ref: CredentialRef, tenant_id: int,
          purpose_code: str, actor_id: uuid) -> ResolvedCredential
    — Resolves a credential reference to its actual value.
    — Requires valid purpose_code for Phase 4 eligibility gating.
    — Returns the resolved credential in memory only.
    — Never logs, persists, or transmits the resolved value.
    — Raises CredentialNotFoundError if the reference does not exist.
    — Raises EligibilityDeniedError if Phase 4 gate blocks release.
    — Raises CredentialExpiredError if the credential has expired.

  store(credential_ref: CredentialRef, value: str,
        credential_type: str, tenant_id: int,
        metadata: Optional[dict] = None) -> CredentialMetadata
    — Stores a new credential or updates an existing one.
    — Never returns the stored value.
    — Returns metadata only (id, type, created_at, expires_at).

  revoke(credential_id: uuid, tenant_id: int, reason: str) -> bool
    — Revokes a credential. Revoked credentials cannot be resolved.
    — Returns true if revocation succeeded.

  list(tenant_id: int, credential_type: Optional[str] = None) -> List[CredentialMetadata]
    — Lists credential metadata for a tenant.
    — Never returns credential values.

CredentialRef:
  credential_id: uuid             — Unique credential identifier (if known)
  alias: string | null            — Human-readable alias (e.g., "whatsapp_api_token")
  tenant_id: integer              — Owning tenant

ResolvedCredential:
  value: str                      — The resolved credential value (in memory only)
  type: string                    — "api_token" | "password" | "oauth_token" | "ssh_key" | "basic_auth"
  expires_at: datetime | null     — Credential expiry time
  metadata: dict                  — Additional credential metadata

CredentialMetadata:
  credential_id: uuid             — Unique credential identifier
  alias: string                   — Human-readable alias
  type: string                    — Credential type
  tenant_id: integer              — Owning tenant
  created_at: datetime            — When the credential was stored
  expires_at: datetime | null     — When the credential expires
  status: string                  — "active" | "revoked" | "expired"
  last_resolved_at: datetime | null — Last resolution timestamp (not the value)
```

### Security Model

| Property | Guarantee | Implementation |
|----------|-----------|----------------|
| **Encryption at rest** | All stored credential values are encrypted | AES-256-GCM encryption before storage. Encryption key managed by the infrastructure platform, not by the Credential Store itself |
| **Encryption in transit** | Credential values are encrypted during resolution | Resolved values returned over in-process API (no network transit in Phase 2). Future distributed deployment requires mTLS |
| **Access control** | Only the Executor Engine may resolve credentials | Authentication of caller identity. No other engine may call `resolve()` |
| **Audit logging** | All credential operations are audited | Every `resolve`, `store`, `revoke` operation logged with actor_id, tenant_id, credential_id, operation_type, timestamp. The resolved value is never logged |
| **No value in logs** | Credential values must never appear in any log | Resolved values are held in memory only, discarded after task completion. Logs contain credential_id and alias only |
| **Tenant isolation** | Credentials are scoped per tenant | All operations include tenant_id. Tenant A cannot resolve Tenant B's credentials |
| **Expiry** | Credentials expire automatically | Each credential has an `expires_at`. Resolution of expired credentials returns `CredentialExpiredError` |
| **Phase 4 integration** | Credential release requires purpose-based eligibility | `resolve()` takes a `purpose_code` and checks Phase 4 eligibility before releasing the value. If the purpose is not authorized, returns `EligibilityDeniedError` |

### Supported Credential Types

| Type | Description | Example |
|------|-------------|---------|
| `api_token` | Bearer token or API key for service authentication | WhatsApp Business API token |
| `password` | Password for basic authentication | SMTP server password |
| `oauth_token` | OAuth 2.0 access token (with optional refresh) | Gmail API OAuth token |
| `ssh_key` | SSH private key for server authentication | Deployment server key |
| `basic_auth` | Username + password pair for HTTP Basic Auth | API gateway credentials |

### Credential Lifecycle

```
Active ──[revoke]──→ Revoked
   │                     │
   │                     └──[renew]──→ Active
   │
   └──[expire]──→ Expired
                     │
                     └──[renew]──→ Active
```

| State | Meaning | Is Terminal? |
|-------|---------|-------------|
| Active | Credential is usable for resolution | No |
| Revoked | Credential has been manually revoked; cannot be resolved | No |
| Expired | Credential has passed its expires_at date; cannot be resolved | No |

### Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Credential not found | CredentialRef does not match any stored credential | Lookup by ID/alias returns empty | Resolution fails with CredentialNotFoundError | Verify credential reference; check tenant scoping |
| Eligibility denied | Phase 4 gate blocks release for the given purpose_code | Phase 4 API returns denied | Resolution fails with EligibilityDeniedError | Request with different purpose_code; escalate to human |
| Credential expired | Credential has passed expires_at | Expiry check on resolve | Resolution fails with CredentialExpiredError | Renew credential; update stored value |
| Encryption failure | Key unavailable or decryption error | Decryption exception | Resolution fails; credential inaccessible | Escalate to infrastructure team |
| Concurrent revocation | Credential revoked between store and resolve | Status check at resolve | Resolution returns revoked error | Retry with renewed credential |

### Storage

The Credential Store uses a dedicated database table (separate from Knowledge Engine and Governance Engine stores) for credential metadata. Credential values are encrypted before storage; metadata (id, alias, type, tenant_id, status, timestamps) is stored in plaintext.

```
credential_metadata:
  credential_id: UUID (PK)
  alias: VARCHAR(255)
  credential_type: VARCHAR(60)
  tenant_id: INTEGER
  status: VARCHAR(20) — "active" | "revoked" | "expired"
  encrypted_value: BYTEA
  encryption_key_id: VARCHAR(60)
  created_at: TIMESTAMP
  expires_at: TIMESTAMP | NULL
  last_resolved_at: TIMESTAMP | NULL
  metadata: JSONB
```

### Integration with ES-005 (Executor Engine)

The Credential Store interface is defined within ES-005's scope. The Executor Engine's credential resolution flow (ES-005 §3) is:

```
1. Task references a credential by ID or alias (CredentialRef)
2. Executor calls CredentialStore.resolve(credential_ref, tenant_id, purpose_code, actor_id)
3. CredentialStore checks Phase 4 eligibility (purpose_code)
4. If eligible: CredentialStore decrypts and returns ResolvedCredential (in memory)
5. Executor passes credential value to channel adapter for authentication
6. Credential is discarded after task completes (never stored in plan payload, event, or log)
7. If ineligible: CredentialStore returns EligibilityDeniedError
```

---

## Options Considered

### Option 1: Internal Service within ES-005 (Chosen)

**Description:** The Credential Store is defined as an internal service dependency of the Executor Engine. Its interface is specified within ES-005's scope as a supporting component, not as an independent engine specification.

**Pros:**
- Consistent with SUPPORTING_ARCHITECTURE_JUSTIFICATION.md classification (Shared Infrastructure)
- No new engine specification required
- Interface contract is clear and minimal
- Least Authority Principle naturally enforced (only Executor can access)
- Phase 4 integration explicitly defined at the interface boundary

**Cons:**
- The Credential Store implementation must be built as part of Executor Engine implementation
- Interface definition is in ES-005 rather than a standalone spec (but this is by design — it is an internal service)

### Option 2: Independent Engine Specification (Rejected)

**Description:** Create ES-011: Credential Store Engine with full engine specification.

**Pros:**
- Formal specification with state machine, events, failure modes, verification

**Cons:**
- **Inconsistent with architecture classification.** SUPPORTING_ARCHITECTURE_JUSTIFICATION.md Component 2 explicitly classifies the Credential Store as Shared Infrastructure, not an engine. Creating an engine specification would contradict G2.2.
- **Over-engineered.** The Credential Store has no compounding intelligence, no semantic lifecycle, and a single consumer (Executor). It does not need a full engine specification.
- **Would require constitutional override.** The architecture classification decision (G2.2, Component 2) would need to be reversed.

### Option 3: Architecture Standard (Separate Document)

**Description:** Define the Credential Store as a standalone Architecture Standard document (like this ADR but elevated to a permanent standard).

**Pros:**
- Standalone reference document

**Cons:**
- Unnecessary indirection — the interface is simple enough to define within ES-005
- All consumers (Executor) and all constraints (ES-005) are already in one place
- SUPPORTING_ARCHITECTURE_JUSTIFICATION.md already recommends "interface definition within ES-005 or short Architecture Standard"

---

## Consequences

### Positive

- Executor Engine can now reference a defined credential resolution contract
- All 10 engine specifications' "Never access credentials" SHALL NEVER clauses are enforceable — only Executor may call `resolve()`
- Phase 4 (Privacy) integration is specified at the credential release boundary
- Least Authority Principle is operationalized — credentials are scoped per tenant, per purpose
- No credential leakage — values never appear in logs, plans, events, or audit trails
- Encryption at rest ensures stored credentials are protected even if the database is compromised

### Negative

- Credential Store must be built before the Executor Engine can function (blocking dependency for ES-005 implementation)
- No existing implementation — entirely greenfield
- Encryption key management (key rotation, key availability) adds operational complexity

### Neutral

- Interface is specified within ES-005's scope — no new engine specification or architectural standard file needed
- Credential Store is not part of the intelligence pipeline — it is operational infrastructure
- Future distributed deployment (if credentials need to be resolved from a separate service) would require the in-process API to be replaced with a network protocol — but the interface contract remains the same

---

## Compliance

### Constitutional Principles Affected

- **§6.3 — Principle of Least Authority:** The Credential Store implements this principle by restricting credential access to the Executor Engine only, and only at execution time.
- **§6.5 — Explainable Decisions:** Credential resolution is not a decision-making process — it is infrastructure. However, audit logging ensures credential access is traceable.
- **§12 (Privacy — System Flow):** Phase 4 integration ensures credentials are only released for authorized purposes.

### Engineering Constitution Articles Affected

- **Article 3 — Separation of Concerns:** The Credential Store is explicitly not an engine — it is shared infrastructure. It does not perform any engine's responsibility.
- **Article 3.3 — No Credential Leakage Across Layers:** This specification directly implements this article by ensuring credentials never cross layer boundaries except through the defined resolve contract at execution time.
- **Article 9 — Scope Discipline:** The Credential Store's scope is minimal — resolve credentials for the Executor only. No feature creep.

---

## Verification

- [ ] CredentialStore API contract implemented — resolve, store, revoke, list
- [ ] Encryption at rest using AES-256-GCM verified
- [ ] Phase 4 integration — resolve() checks purpose_code eligibility before releasing credential
- [ ] Tenant isolation — Tenant A cannot resolve Tenant B's credentials
- [ ] No credential values in logs — log inspection confirms only credential_id, alias, operation_type, timestamp
- [ ] Only Executor Engine may call resolve() — caller identity authentication verified
- [ ] Credential expiry enforced — resolve() of expired credential returns CredentialExpiredError
- [ ] Revocation enforced — resolve() of revoked credential returns error
- [ ] ES-005 integration verified — credential resolution flow works end-to-end (resolve → pass to adapter → discard)
- [ ] Credential metadata table schema matches specification

---

## References

- [SHUNYA_ARCHITECTURE.md](/SHUNYA_ARCHITECTURE.md) — Section 6.3 (Principle of Least Authority)
- [SHUNYA_SYSTEM_FLOW.md](/architecture/SHUNYA_SYSTEM_FLOW.md) — Section 12 (Secrets, Privacy, Least Privilege)
- [ES-005: Executor Engine](/governance/engine_specs/ES-005-EXECUTOR-ENGINE.md) — Credential resolution flow, execution preparation, failure modes
- [ARCHITECTURE_BASELINE_REVIEW.md](/architecture/ARCHITECTURE_BASELINE_REVIEW.md) — M2 (Credential Store Interface Not Defined), ADR-003
- [ARCHITECTURE_FINDINGS_CLASSIFICATION.md](/architecture/ARCHITECTURE_FINDINGS_CLASSIFICATION.md) — M2/R4/ADR-003
- [SUPPORTING_ARCHITECTURE_JUSTIFICATION.md](/architecture/SUPPORTING_ARCHITECTURE_JUSTIFICATION.md) — Component 2 (Credential Store — Shared Infrastructure)