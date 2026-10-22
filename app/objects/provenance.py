"""Creation provenance for canonical business objects (G1.24, decision D-1 = B).

Why a persisted field and not a heuristic
----------------------------------------
Onboarding provisions 26 placeholder records ("Customer", "Invoice", …) so the
workspace is never visually empty. Before this module those rows were ordinary
``sh_objects`` rows with no marker, so every consumer — the first-use predicate,
Executive Home, and the AI grounding path — had to answer "has the user given us
anything?" from the *existence* of rows. It answered "yes" for a brand-new
tenant. Counting rows cannot be made truthful by inspecting them later: a
placeholder the user has edited and a placeholder they have not are
indistinguishable after the fact.

So the *act of creation* records its origin, once, at write time:

============ ===============================================================
provenance   meaning
============ ===============================================================
user         created by an authenticated user action (API, UI, upload)
import       created by a bulk import / integration sync
ai           created by the AI on the user's behalf
onboarding_seed  provisioned placeholder; NOT user-supplied business data
system       created by an audited system path (bootstrap, migration tool)
NULL         unknown historical provenance (rows written before G1.24)
============ ===============================================================

Decisions this encodes
----------------------
* **D-1 (Option B):** only ``onboarding_seed`` is excluded from "meaningful
  business data". Every other value counts, including ``ai`` and ``import``:
  the user asked for those records even if they did not type them.
* **Unknown stays unknown.** NULL is never rewritten by guesswork. A NULL row
  counts as business data — over-counting user data is recoverable; hiding a
  tenant's real records from first-use and from AI grounding is not.
* **D-2 (No):** examples are not organizational knowledge. The AI grounding
  boundary filters ``onboarding_seed`` rows out; see ``grounding_allowed_clause``.

Nothing here deletes, converts or relabels an existing row. Rows that predate
the field keep NULL until an operator establishes provenance with evidence.
"""

from __future__ import annotations

from typing import Optional

#: Canonical provenance vocabulary. Store exactly these strings.
PROVENANCE_USER = "user"
PROVENANCE_IMPORT = "import"
PROVENANCE_AI = "ai"
PROVENANCE_ONBOARDING_SEED = "onboarding_seed"
PROVENANCE_SYSTEM = "system"

VALID_PROVENANCES = frozenset({
    PROVENANCE_USER,
    PROVENANCE_IMPORT,
    PROVENANCE_AI,
    PROVENANCE_ONBOARDING_SEED,
    PROVENANCE_SYSTEM,
})

#: Provenances that count as user-supplied business data. ``None`` (unknown)
#: counts too — see the module docstring.
NON_BUSINESS_PROVENANCES = frozenset({PROVENANCE_ONBOARDING_SEED})


class InvalidProvenanceError(ValueError):
    """Raised when a caller supplies a provenance value outside the vocabulary."""


def normalise_provenance(value: Optional[str]) -> Optional[str]:
    """Return the canonical value, or raise. ``None`` legitimately means unknown.

    An unknown *non-empty* string is a programming error, not a new category:
    accepting it would let a typo ("onboardingseed") quietly become business
    data and defeat the whole mechanism.
    """
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text not in VALID_PROVENANCES:
        raise InvalidProvenanceError(
            f"unknown provenance {value!r}; expected one of "
            f"{sorted(VALID_PROVENANCES)} or None (unknown)"
        )
    return text


def is_example(provenance: Optional[str]) -> bool:
    """True when the row is a provisioned example rather than user data."""
    return (provenance or "").strip().lower() in NON_BUSINESS_PROVENANCES


def counts_as_business_data(provenance: Optional[str]) -> bool:
    """True when the row should satisfy the first-use predicate."""
    return not is_example(provenance)


def grounding_allowed_clause(column: str = "provenance") -> str:
    """SQL predicate for "may this row be used as organizational fact?".

    D-2: system-generated examples must not be presented to AI as verified facts
    about the organization. This is the single clause every grounding query uses,
    so the exclusion lives at the retrieval boundary rather than in a prompt.

    Unknown (NULL) history is allowed: it is not *known* to be an example, and
    suppressing a tenant's real data on a guess would be the worse error. The
    caller is responsible for the column name (it varies by query).
    """
    return f"({column} IS NULL OR {column} <> '{PROVENANCE_ONBOARDING_SEED}')"


def annotate(row: dict) -> dict:
    """Add the UI-facing provenance fields to a serialized object row.

    Applied at the JSON boundary so every surface (list, detail, search) labels
    an example the same way. Returns the same dict for convenient chaining.
    """
    if not isinstance(row, dict):
        return row
    prov = row.get("provenance")
    row["is_example"] = is_example(prov)
    row["provenance_label"] = provenance_label(prov)
    return row


def provenance_label(provenance: Optional[str]) -> str:
    """Human/UI-facing label. Never claims more than the stored value."""
    mapping = {
        PROVENANCE_USER: "Created by you",
        PROVENANCE_IMPORT: "Imported",
        PROVENANCE_AI: "Created by SHUNYA AI",
        PROVENANCE_ONBOARDING_SEED: "Example",
        PROVENANCE_SYSTEM: "Created by the system",
    }
    return mapping.get((provenance or "").strip().lower(), "Source unknown")
