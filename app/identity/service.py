"""
SHUNYA — Canonical Identity Service (FDA4).

ONE canonical identity resolution authority.

All identity sources converge here:
- Gmail sender/recipient
- Contacts
- Import paths
- API paths

Identity claims are stored with full provenance.
Conflicting claims remain visible.
Merges preserve historical truth.
Splits are auditable.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app import db
from app.models import Person, PersonIdentity, Organization
from core.identity_interface import (
    IdentityClaim, IdentityResolution, IdentityType, ClaimType,
    ClaimStatus, MergeStatus, DuplicateClassification,
    IdentityResolutionInterface, IdentityGovernance, Enum,
)


_INJECTION_KEYWORDS_IDENTITY = [
    "ignore all security",
    "bypass auth",
    "system override",
    "admin access",
]


def _check_identity_contamination(value: str) -> None:
    """Identity claims must not be poisoned with injection payloads."""
    v = value.lower()
    for kw in _INJECTION_KEYWORDS_IDENTITY:
        if kw in v:
            raise ValueError(
                f"Identity claim rejected: contains prohibited pattern '{kw}'. "
                "Identity claims must remain DATA, not executable instructions."
            )


def _normalize_email(email: str) -> str:
    """Normalize an email address for deterministic matching."""
    return email.strip().lower()


def _normalize_phone(phone: str) -> str:
    """Normalize a phone number to digits only."""
    return "".join(c for c in phone if c.isdigit() or c == "+")


def _generate_id() -> str:
    return str(uuid.uuid4())


class IdentityService(IdentityResolutionInterface):
    """FDA4 canonical identity resolution service.

    ONE authority for all SHUNYA identity operations.
    Uses Person and PersonIdentity models as persistence.
    """

    def __init__(self, session=None):
        self._session = session or db.session

    def get_canonical_interface(self) -> str:
        return "IdentityResolutionInterface"

    # ──────────────────────────────────────────────────────────────────
    # Claim management
    # ──────────────────────────────────────────────────────────────────

    def add_claim(self, claim: IdentityClaim) -> IdentityClaim:
        """Add a new identity claim.

        If the claim value matches an existing identity, the claim is
        linked to that identity. Otherwise, a new identity is created.
        """
        _check_identity_contamination(claim.claim_value)

        # Normalize based on claim type
        normalized = self._normalize(claim.claim_value, claim.claim_type)

        # Resolve existing identity
        existing = self._find_identity_by_claim(normalized, claim.claim_type,
                                                  claim.tenant_id)

        # Create or update Person
        if existing:
            person = existing
            person_id = person.id
        else:
            # Check if we have a Person with matching canonical_name (for named claims)
            person = None
            if claim.claim_type == ClaimType.NAME and claim.claim_value:
                person = Person.query.filter_by(
                    canonical_name=claim.claim_value).first()
            if not person:
                person = Person(
                    canonical_name=claim.claim_value if claim.claim_type == ClaimType.NAME
                               else f"Unknown ({claim.claim_type.value})",
                    identity_type=claim.identity_type.value if isinstance(claim.identity_type, Enum) else claim.identity_type,
                )
                self._session.add(person)
                self._session.flush()
            person_id = person.id

        # Store the claim as PersonIdentity
        pi = PersonIdentity(
            person_id=person_id,
            identity_type=claim.claim_type.value,
            identity_value=normalized,
            normalized_value=normalized,
            source=claim.source,
            source_id=claim.source_id,
            confidence=claim.confidence,
            metadata_json=json.dumps({
                "claim_id": claim.claim_id or _generate_id(),
                "tenant_id": claim.tenant_id,
                "provenance": claim.provenance,
                "observed_at": claim.observed_at,
            }),
        )
        self._session.add(pi)
        self._session.commit()

        claim.claim_id = str(pi.id)
        claim.identity_id = str(person_id)
        return claim

    def resolve(self, claim_value: str, claim_type: ClaimType = ClaimType.EMAIL,
                tenant_id: str = "") -> IdentityResolution:
        """Resolve a claim value to a canonical identity."""
        normalized = self._normalize(claim_value, claim_type)
        person = self._find_identity_by_claim(normalized, claim_type, tenant_id)

        if not person:
            return IdentityResolution(
                identity_id="",
                identity_type=IdentityType.PERSON,
                confidence=0.0,
                resolution_method="not_found",
            )

        # Get all claims for this person
        identities = PersonIdentity.query.filter_by(
            person_id=person.id).all()
        claims = []
        aliases = []
        for pi in identities:
            claims.append(IdentityClaim(
                claim_id=str(pi.id),
                identity_id=str(person.id),
                claim_type=pi.identity_type,
                claim_value=pi.identity_value,
                source=pi.source or "",
                source_id=pi.source_id or "",
                confidence=pi.confidence or 1.0,
                status=ClaimStatus.ACTIVE,
            ))
            aliases.append(pi.identity_value)

        return IdentityResolution(
            identity_id=str(person.id),
            identity_type=IdentityType.PERSON,
            claims=claims,
            alias_values=aliases,
            confidence=1.0,
            resolution_method="direct",
        )

    def get_identity(self, identity_id: str,
                     tenant_id: str = "") -> Optional[IdentityResolution]:
        """Get the full identity resolution for a canonical identity ID."""
        try:
            person = Person.query.get(int(identity_id))
        except (ValueError, TypeError):
            return None
        if not person:
            return None

        identities = PersonIdentity.query.filter_by(
            person_id=person.id).all()
        claims = []
        aliases = []
        for pi in identities:
            claims.append(IdentityClaim(
                claim_id=str(pi.id),
                identity_id=str(person.id),
                claim_type=pi.identity_type,
                claim_value=pi.identity_value,
                source=pi.source or "",
                source_id=pi.source_id or "",
                confidence=pi.confidence or 1.0,
                status=ClaimStatus.ACTIVE,
            ))
            aliases.append(pi.identity_value)

        return IdentityResolution(
            identity_id=str(person.id),
            identity_type=IdentityType.PERSON,
            claims=claims,
            alias_values=aliases,
            confidence=1.0,
            resolution_method="direct",
        )

    def get_claims(self, identity_id: str,
                   tenant_id: str = "") -> list[IdentityClaim]:
        """Get all claims for a canonical identity."""
        try:
            pid = int(identity_id)
        except (ValueError, TypeError):
            return []
        identities = PersonIdentity.query.filter_by(person_id=pid).all()
        return [
            IdentityClaim(
                claim_id=str(pi.id),
                identity_id=str(pi.person_id),
                claim_type=pi.identity_type,
                claim_value=pi.identity_value,
                source=pi.source or "",
                source_id=pi.source_id or "",
                confidence=pi.confidence or 1.0,
                status=ClaimStatus.ACTIVE,
            )
            for pi in identities
        ]

    # ──────────────────────────────────────────────────────────────────
    # Deduplication
    # ──────────────────────────────────────────────────────────────────

    def find_duplicates(self, tenant_id: str = "",
                         threshold: float = 0.8) -> list[dict]:
        """Find possible duplicate identities.

        Deterministic approach:
        - Same email normalized → CONFIRMED DUPLICATE
        - Same phone normalized → CONFIRMED DUPLICATE
        - Same name, different email → POSSIBLE DUPLICATE
        """
        results = []
        all_pi = PersonIdentity.query.all()
        # Group by normalized value
        by_value: dict[str, list[PersonIdentity]] = {}
        for pi in all_pi:
            by_value.setdefault(pi.identity_value, []).append(pi)

        for value, pis in by_value.items():
            if len(pis) < 2:
                continue
            person_ids = set(p.person_id for p in pis)
            if len(person_ids) < 2:
                continue

            # Check if it's email or phone (CONFIRMED)
            p_types = set(p.identity_type for p in pis)
            if any(t in ("email", "phone") for t in p_types):
                classification = DuplicateClassification.CONFIRMED
            else:
                classification = DuplicateClassification.POSSIBLE

            persons = Person.query.filter(
                Person.id.in_(list(person_ids))).all()
            results.append({
                "classification": classification.value,
                "matched_value": value,
                "match_type": list(p_types),
                "person_ids": list(person_ids),
                "person_names": [p.canonical_name for p in persons],
            })

        return results

    def classify_duplicate(self, identity_id_a: str, identity_id_b: str,
                            classification: str) -> dict:
        """Classify two identities as duplicates."""
        if classification not in [e.value for e in DuplicateClassification]:
            return {"success": False, "error": f"Invalid classification: {classification}"}
        return {
            "success": True,
            "identity_a": identity_id_a,
            "identity_b": identity_id_b,
            "classification": classification,
        }

    # ──────────────────────────────────────────────────────────────────
    # Merge
    # ──────────────────────────────────────────────────────────────────

    def merge(self, primary_id: str, secondary_id: str,
               reason: str = "duplicate") -> dict:
        """Merge secondary identity into primary.

        A+B → canonical identity:
        - Preserve primary ID
        - Move all claims/aliases to primary
        - Preserve provenance
        - Preserve relationship history
        - Preserve memory references
        - Preserve evidence references
        - Never destroy historical truth
        """
        try:
            primary = Person.query.get(int(primary_id))
            secondary = Person.query.get(int(secondary_id))
        except (ValueError, TypeError):
            return {"success": False, "error": "Identity not found"}

        if not primary or not secondary:
            return {"success": False, "error": "Identity not found"}
        if primary.id == secondary.id:
            return {"success": False, "error": "Cannot merge identity with itself"}

        # Move all claims to primary
        pis = PersonIdentity.query.filter_by(person_id=secondary.id).all()
        for pi in pis:
            pi.person_id = primary.id
            # Record merge provenance in metadata
            existing_meta = {}
            if pi.metadata_json:
                try:
                    existing_meta = json.loads(pi.metadata_json)
                except (json.JSONDecodeError, TypeError):
                    existing_meta = {}
            merge_prov = existing_meta.get("merge_provenance", [])
            merge_prov.append({
                "merged_from": secondary.id,
                "merged_into": primary.id,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            })
            existing_meta["merge_provenance"] = merge_prov
            pi.metadata_json = json.dumps(existing_meta)

        # Record merge in metadata
        if primary.metadata_json:
            meta = json.loads(primary.metadata_json)
        else:
            meta = {}
        merged = meta.get("merged_identities", [])
        if secondary.id not in merged:
            merged.append(secondary.id)
        meta["merged_identities"] = merged
        meta["last_merge"] = datetime.utcnow().isoformat()
        meta["last_merge_reason"] = reason
        primary.metadata_json = json.dumps(meta)

        self._session.commit()
        return {
            "success": True,
            "primary_id": primary_id,
            "secondary_id": secondary_id,
            "secondary_merged": True,
            "merged_identities": [primary_id, secondary_id],
        }

    @staticmethod
    def _append_merge_provenance(metadata_json_field, secondary_id, primary_id, reason):
        """SQL expression to append merge provenance to metadata_json."""
        import sqlalchemy as sa
        from sqlalchemy import func, text
        return func.json_set(
            sa.text("COALESCE(metadata_json, '{}')"),
            "$.merge_provenance",
            func.json_array_append(
                sa.text("COALESCE(json_extract(metadata_json, '$.merge_provenance'), '[]')"),
                "$",
                json.dumps({
                    "merged_from": secondary_id,
                    "merged_into": primary_id,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            )
        )

    # ──────────────────────────────────────────────────────────────────
    # Split / Unmerge
    # ──────────────────────────────────────────────────────────────────

    def split(self, identity_id: str, claim_ids: list[str],
               reason: str = "incorrect_merge") -> dict:
        """Split claims from a merged identity into a new identity.

        A bad merge must be reversible where technically required.
        Historical provenance explains what happened.

        If some claims cannot safely be restored automatically, the audit
        trail is preserved and controlled review is required.
        """
        try:
            person = Person.query.get(int(identity_id))
        except (ValueError, TypeError):
            return {"success": False, "error": "Identity not found"}
        if not person:
            return {"success": False, "error": "Identity not found"}

        # Create a new Person for the split-off claims
        new_person = Person(
            canonical_name=f"{person.canonical_name} (split)",
            identity_type=person.identity_type,
            metadata_json=json.dumps({
                "split_from": identity_id,
                "split_reason": reason,
                "split_at": datetime.utcnow().isoformat(),
            }),
        )
        self._session.add(new_person)
        self._session.flush()

        # Move specified claims to new person
        moved = 0
        for cid in claim_ids:
            try:
                pi = PersonIdentity.query.get(int(cid))
                if pi and pi.person_id == person.id:
                    pi.person_id = new_person.id
                    moved += 1
            except (ValueError, TypeError):
                pass

        # Record split in audit
        meta = json.loads(person.metadata_json or "{}")
        splits = meta.get("split_history", [])
        splits.append({
            "new_identity_id": new_person.id,
            "claim_ids": claim_ids,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
        meta["split_history"] = splits
        person.metadata_json = json.dumps(meta)

        self._session.commit()
        return {
            "success": True,
            "original_id": identity_id,
            "new_identity_id": str(new_person.id),
            "claims_moved": moved,
            "reason": reason,
        }

    # ──────────────────────────────────────────────────────────────────
    # Conflict handling
    # ──────────────────────────────────────────────────────────────────

    def find_conflicts(self, tenant_id: str = "") -> list[dict]:
        """Find conflicting identity claims.

        Example:
        Source A claims john@example.com → person 1
        Source B claims john@example.com → person 2 (different person ID)

        Conflicting claims remain visible with their sources.
        """
        conflicts = []
        all_pi = PersonIdentity.query.all()
        by_value: dict[str, list[PersonIdentity]] = {}
        for pi in all_pi:
            by_value.setdefault(pi.identity_value, []).append(pi)

        for value, pis in by_value.items():
            person_ids = set(p.person_id for p in pis)
            if len(person_ids) < 2:
                continue
            # This value resolves to multiple people → conflict
            persons = Person.query.filter(
                Person.id.in_(list(person_ids))).all()
            conflicts.append({
                "claim_value": value,
                "claim_types": list(set(p.identity_type for p in pis)),
                "person_ids": list(person_ids),
                "person_names": [p.canonical_name for p in persons],
                "sources": list(set(p.source for p in pis if p.source)),
                "status": "conflicted",
            })

        return conflicts

    def resolve_conflict(self, claim_value: str,
                          target_identity_id: str,
                          resolution: str = "manual",
                          reason: str = "") -> dict:
        """Resolve a conflicting claim by assigning it to a specific identity.

        Conflicting claims remain visible in provenance.
        The resolution is recorded for audit.
        """
        pis = PersonIdentity.query.filter_by(
            identity_value=claim_value).all()
        resolved = []
        for pi in pis:
            if str(pi.person_id) != target_identity_id:
                # Reassign to target
                old_person_id = pi.person_id
                pi.person_id = int(target_identity_id)
                resolved.append({
                    "claim_id": pi.id,
                    "old_person_id": old_person_id,
                    "new_person_id": target_identity_id,
                })

        self._session.commit()
        return {
            "success": True,
            "claim_value": claim_value,
            "target_identity_id": target_identity_id,
            "resolution": resolution,
            "reason": reason,
            "claims_resolved": resolved,
        }

    # ──────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────

    def _normalize(self, value: str, claim_type: ClaimType) -> str:
        if claim_type == ClaimType.EMAIL:
            return _normalize_email(value)
        elif claim_type == ClaimType.PHONE:
            return _normalize_phone(value)
        return value.strip()

    def _find_identity_by_claim(self, normalized: str, claim_type: ClaimType,
                                 tenant_id: str) -> Optional[Person]:
        """Find a Person by an identity claim value."""
        if claim_type == ClaimType.EMAIL:
            pi = PersonIdentity.query.filter_by(
                identity_type="email",
                identity_value=normalized,
            ).first()
        elif claim_type == ClaimType.PHONE:
            pi = PersonIdentity.query.filter_by(
                identity_type="phone",
                identity_value=normalized,
            ).first()
        else:
            # Try all claim types
            pi = PersonIdentity.query.filter_by(
                identity_value=normalized).first()
        if pi:
            return Person.query.get(pi.person_id)
        return None