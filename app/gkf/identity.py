"""GKF — Identity generation, validation, and parsing.

All GKF identities follow a hierarchical scheme with two critical rules:

1. **Structural identities** encode their position in the document hierarchy
   (e.g., gkc_shunya_constitution:vol_1, gkc_shunya_constitution:art_1)

2. **Semantic identities (PRINCIPLE) are STABLE** — they do NOT encode
   document location. A principle's identity is a slug that survives
   any document reorganization.
   (e.g., gkc_shunya_constitution:pr_human_first — never changes)

Identity format:
    <collection_id>:[<volume_id>:[<chapter_id>:]]<element_type>_<local_id>
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def _slugify(name: str) -> str:
    """Convert a name to a slug suitable for identity components."""
    return name.lower().replace(" ", "_").replace("-", "_")


def sanitize_name(name: str) -> str:
    """Sanitize a collection or volume name for identity usage."""
    return _slugify(name)


# ---- Collection identity ----

def generate_collection_id(name: str) -> str:
    """Generate a GovernedCollection identity from its name.

    Format: gkc_<sanitized_name>
    Example: gkc_shunya_constitution
    """
    return f"gkc_{sanitize_name(name)}"


# ---- Structural identities ----

def generate_volume_id(collection_id: str, number: int) -> str:
    """Generate a Volume identity.

    Format: <collection_id>:vol_<number>
    Example: gkc_shunya_constitution:vol_1
    """
    return f"{collection_id}:vol_{number}"


def generate_chapter_id(volume_id: str, number: int) -> str:
    """Generate a Chapter identity within a Volume.

    Format: <volume_id>:ch_<number>
    Example: gkc_shunya_constitution:vol_1:ch_1
    """
    return f"{volume_id}:ch_{number}"


def generate_article_id(collection_id: str, number: int) -> str:
    """Generate an Article identity.

    Format: <collection_id>:art_<number>
    Example: gkc_shunya_constitution:art_1

    Article identity includes the article number for human readability,
    but implementation references should use Principle identities.
    """
    return f"{collection_id}:art_{number}"


# ---- Semantic identities (STABLE) ----

def generate_principle_id(collection_id: str, name: str) -> str:
    """Generate a Principle identity.

    Format: <collection_id>:pr_<slug>
    Example: gkc_shunya_constitution:pr_human_first

    This identity is STABLE. It does NOT include article number,
    chapter, or volume. It never changes if the principle moves.
    """
    return f"{collection_id}:pr_{sanitize_name(name)}"


def generate_interpretation_id(principle_id: str, number: int) -> str:
    """Generate an Interpretation identity.

    Format: <principle_id>:int_<number>
    Example: gkc_shunya_constitution:pr_human_first:int_1
    """
    return f"{principle_id}:int_{number}"


# ---- Cross-cutting identities ----

def generate_reference_id(source_id: str, target_id: str) -> str:
    """Generate a Reference identity.

    Format: <source_id>:ref_<target_id_hash>
    """
    import hashlib
    target_hash = hashlib.md5(target_id.encode()).hexdigest()[:8]
    return f"{source_id}:ref_{target_hash}"


def generate_evidence_id(collection_id: str, source_type: str, local_id: str) -> str:
    """Generate an Evidence identity.

    Format: <collection_id>:ev_<source_type>_<local_id>
    Example: gkc_shunya_constitution:ev_constitution
    """
    return f"{collection_id}:ev_{_slugify(source_type)}_{_slugify(local_id)}"


def generate_implementation_link_id(principle_id: str, module_path: str) -> str:
    """Generate an ImplementationLink identity.

    Format: <principle_id>:impl_<module_slug>
    """
    return f"{principle_id}:impl_{_slugify(module_path)}"


def generate_amendment_id(target_id: str, number: int) -> str:
    """Generate an Amendment identity.

    Format: <target_id>:amd_<number>
    """
    return f"{target_id}:amd_{number}"


def generate_version_id(element_id: str, number: int) -> str:
    """Generate a Version identity.

    Format: <element_id>:v<number>
    Example: gkc_shunya_constitution:art_1:v1
    """
    return f"{element_id}:v{number}"


# ---- Parsing ----

def parse_gkf_identity(identity: str) -> Dict[str, Any]:
    """Parse a GKF identity into its components.

    Returns:
        dict with keys: full, collection_id, volume_id, chapter_id,
        element_type, local_id

    Raises ValueError if the identity cannot be parsed.
    """
    if not identity or not isinstance(identity, str):
        raise ValueError(f"Invalid GKF identity: {identity!r}")

    result: Dict[str, Any] = {"full": identity}

    # Extract collection_id (always starts with gkc_)
    if not identity.startswith("gkc_"):
        raise ValueError(f"GKF identity must start with 'gkc_': {identity}")

    # Split on colon to get hierarchical parts
    parts = identity.split(":")

    result["collection_id"] = parts[0]

    # Determine element type from the last part
    last_part = parts[-1]

    # Element type prefixes — order matters: more specific prefixes first
    type_prefixes = {
        "impl_": ("implementation_link", "implementation_link_id"),
        "amd_": ("amendment", "amendment_id"),
        "vol_": ("volume", "volume_id"),
        "ch_": ("chapter", "chapter_id"),
        "art_": ("article", "article_id"),
        "pr_": ("principle", "principle_id"),
        "int_": ("interpretation", "interpretation_id"),
        "ref_": ("reference", "reference_id"),
        "ev_": ("evidence", "evidence_id"),
    }

    # Check for version — must be v followed ONLY by digits (not vol_ or similar)
    if last_part.startswith("v") and len(last_part) > 1 and last_part[1:].isdigit():
        result["element_type"] = "gkf_version"
        result["local_id"] = last_part
        if len(parts) >= 2:
            result["element_id"] = ":".join(parts[:-1])
        return result

    for prefix, (elem_type, id_key) in type_prefixes.items():
        if last_part.startswith(prefix):
            result["element_type"] = f"gkf_{elem_type}"
            result["local_id"] = last_part[len(prefix):]
            if id_key:
                result[id_key] = last_part
            break
    else:
        # Fallback — collection itself
        if len(parts) == 1:
            result["element_type"] = "gkf_collection"
            result["local_id"] = parts[0][4:]  # strip gkc_
        else:
            raise ValueError(f"Cannot parse GKF identity: {identity}")

    # Structural hierarchy extraction
    for part in parts[1:]:
        if part.startswith("vol_"):
            result["volume_id"] = part
        elif part.startswith("ch_"):
            result["chapter_id"] = part

    return result


# ---- Validation ----

def is_valid_gkf_identity(identity: str) -> bool:
    """Validate that a string is a well-formed GKF identity."""
    try:
        parse_gkf_identity(identity)
        return True
    except ValueError:
        return False


def is_principle_identity(identity: str) -> bool:
    """Check if an identity is a Principle identity specifically.

    Principle identities are the only semantic identities that
    must be location-independent.
    """
    try:
        parsed = parse_gkf_identity(identity)
        return parsed["element_type"] == "gkf_principle"
    except ValueError:
        return False


def is_principle_identity_stable(identity: str) -> bool:
    """Verify that a Principle identity is stable — does NOT encode
    article number, chapter, or volume in its local_id.
    """
    parsed = parse_gkf_identity(identity)
    if parsed["element_type"] != "gkf_principle":
        return False
    local_id = parsed.get("local_id", "")
    # A stable principle identity's local_id should not contain
    # "art_", "ch_", or "vol_" prefixes
    stable_blockers = ["art_", "ch_", "vol_"]
    return not any(blocker in local_id for blocker in stable_blockers)