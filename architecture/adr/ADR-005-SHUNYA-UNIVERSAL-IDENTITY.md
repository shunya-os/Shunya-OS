# ADR-005 — SHUNYA Universal Identity

**Status:** Proposed
**Date:** 2026-07-21
**Author:** Hermes Agent (Nous Research)
**Supersedes:** ES-010 (Identity Engine)

## Context

The existing Identity Engine (ES-010) resolves identity claims (email, phone, channel) to a canonical person. However, identity is treated as a resolution concern rather than a first-class kernel primitive. The GENESIS directive requires:

1. Identity is not an email address — it owns multiple authentication methods
2. Multiple auth methods (Gmail, Microsoft, Company Email, Phone, Passkey, Apple Login) may authenticate the same identity
3. Identity-linking requires ownership verification, not automatic merging
4. A human always has one SHUNYA Identity
5. Organizations never own identities

## Decision

Implement `SHUNYAIdentity` as a kernel primitive with:
- Immutable internal ID (`sid_` prefix)
- One or more `AuthenticationMethod` records (email, oauth, passkey, phone)
- A linking flow: Detect → Suggest → Verify → Link → Maintain
- Verification via email confirmation, OAuth callback, or cryptographic challenge
- The existing `TeamMember` model becomes a legacy authentication wrapper

## Consequences

- Positive: One identity, many auth methods
- Positive: Identity exists independently of any organization
- Positive: Linking is explicit and verified
- Negative: Backward compatibility with TeamMember-based auth
- Risk: Migration from existing TeamMember records

## Implementation

New `kernel/identity.py` module with `SHUNYAIdentity` and `AuthenticationMethod` types. The existing `IdentityEngine` wraps these for backward compatibility.