"""GKF — Identity generation, validation, and parsing.

All GKF identities follow a hierarchical scheme with two critical rules:

1. **Structural identities** encode their position in the document hierarchy.

2. **Semantic identities (GOVERNING_PRINCIPLE) are STABLE** — they do NOT encode
   document location. A governing principle's identity is a slug that survives
   any document reorganization.

Identity format:
    <collection_id>:[<volume_id>:[<chapter_id>:]]<element_type>_<local_id>
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def sanitize_name(name: str) -> str:
    return _slugify(name)


# ---- Collection ----

def generate_collection_id(name: str) -> str:
    return f"gkc_{sanitize_name(name)}"


# ---- Structural ----

def generate_volume_id(collection_id: str, number: int) -> str:
    return f"{collection_id}:vol_{number}"


def generate_chapter_id(volume_id: str, number: int) -> str:
    return f"{volume_id}:ch_{number}"


def generate_article_id(collection_id: str, number: int) -> str:
    return f"{collection_id}:art_{number}"


# ---- Semantic (STABLE) ----

def generate_governing_principle_id(collection_id: str, name: str) -> str:
    """Generate a Governing Principle identity.

    This identity is STABLE — it does NOT include article number,
    chapter, or volume. It never changes if the principle moves.
    """
    return f"{collection_id}:gp_{sanitize_name(name)}"


def generate_interpretation_id(principle_id: str, number: int) -> str:
    return f"{principle_id}:int_{number}"


# ---- GKF-001A Semantic Enrichment ----

def generate_authority_id(collection_id: str, name: str) -> str:
    return f"{collection_id}:auth_{sanitize_name(name)}"


def generate_citation_id(source_id: str, target_id: str) -> str:
    target_hash = hashlib.md5(target_id.encode()).hexdigest()[:8]
    return f"{source_id}:cit_{target_hash}"


def generate_commentary_id(principle_id: str, number: int) -> str:
    return f"{principle_id}:com_{number}"


def generate_example_id(principle_id: str, number: int) -> str:
    return f"{principle_id}:ex_{number}"


def generate_implementation_guidance_id(principle_id: str, name: str) -> str:
    return f"{principle_id}:guidance_{sanitize_name(name)}"


# ---- Cross-cutting ----

def generate_reference_id(source_id: str, target_id: str) -> str:
    target_hash = hashlib.md5(target_id.encode()).hexdigest()[:8]
    return f"{source_id}:ref_{target_hash}"


def generate_evidence_id(collection_id: str, source_type: str, local_id: str) -> str:
    return f"{collection_id}:ev_{_slugify(source_type)}_{_slugify(local_id)}"


def generate_implementation_link_id(principle_id: str, module_path: str) -> str:
    return f"{principle_id}:impl_{_slugify(module_path)}"


def generate_amendment_id(target_id: str, number: int) -> str:
    return f"{target_id}:amd_{number}"


def generate_version_id(element_id: str, number: int) -> str:
    return f"{element_id}:v{number}"


# ---- Parsing ----

_GKF_TYPE_PREFIXES = {
    "gp_": "gkf_governing_principle",
    "auth_": "gkf_authority",
    "cit_": "gkf_citation",
    "com_": "gkf_commentary",
    "ex_": "gkf_example",
    "guidance_": "gkf_implementation_guidance",
    "impl_": "gkf_implementation_link",
    "amd_": "gkf_amendment",
    "vol_": "gkf_volume",
    "ch_": "gkf_chapter",
    "art_": "gkf_article",
    "pr_": "gkf_governing_principle",  # legacy alias
    "int_": "gkf_interpretation",
    "ref_": "gkf_reference",
    "ev_": "gkf_evidence",
}


def parse_gkf_identity(identity: str) -> Dict[str, Any]:
    if not identity or not isinstance(identity, str):
        raise ValueError(f"Invalid GKF identity: {identity!r}")

    result: Dict[str, Any] = {"full": identity}

    if not identity.startswith("gkc_"):
        raise ValueError(f"GKF identity must start with 'gkc_': {identity}")

    parts = identity.split(":")
    result["collection_id"] = parts[0]
    last_part = parts[-1]

    # Version check: v followed ONLY by digits
    if last_part.startswith("v") and len(last_part) > 1 and last_part[1:].isdigit():
        result["element_type"] = "gkf_version"
        result["local_id"] = last_part
        if len(parts) >= 2:
            result["element_id"] = ":".join(parts[:-1])
        return result

    for prefix, elem_type in _GKF_TYPE_PREFIXES.items():
        if last_part.startswith(prefix):
            result["element_type"] = elem_type
            result["local_id"] = last_part[len(prefix):]
            break
    else:
        if len(parts) == 1:
            result["element_type"] = "gkf_collection"
            result["local_id"] = parts[0][4:]
        else:
            raise ValueError(f"Cannot parse GKF identity: {identity}")

    for part in parts[1:]:
        if part.startswith("vol_"):
            result["volume_id"] = part
        elif part.startswith("ch_"):
            result["chapter_id"] = part

    return result


# ---- Validation ----

def is_valid_gkf_identity(identity: str) -> bool:
    try:
        parse_gkf_identity(identity)
        return True
    except ValueError:
        return False


def is_governing_principle_identity(identity: str) -> bool:
    try:
        parsed = parse_gkf_identity(identity)
        return parsed["element_type"] == "gkf_governing_principle"
    except ValueError:
        return False


def is_principle_identity_stable(identity: str) -> bool:
    parsed = parse_gkf_identity(identity)
    if parsed["element_type"] != "gkf_governing_principle":
        return False
    local_id = parsed.get("local_id", "")
    blockers = ["art_", "ch_", "vol_"]
    return not any(b in local_id for b in blockers)