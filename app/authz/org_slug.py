"""Organization slug generation — one implementation for every creation path.

Why this module exists
----------------------
``organizations.slug`` is the organization's URL identity and, since
``r6b34_identity_integrity``, a database-enforced unique index. Two creation
routes existed with different behaviour:

* ``app/production/identity/org_routes.py`` generated a sanitized slug and
  appended a counter until it was free;
* ``app/routes.py`` (the route the SPA onboarding flow actually calls) did
  ``company_name.lower().replace(" ", "-")[:50]`` with no sanitization and no
  uniqueness check.

The second one therefore produced collisions for any two organizations sharing a
name — silently duplicated before the unique index existed, and a raw
``IntegrityError``/HTTP 500 afterwards. Neither is acceptable: the user asked for
an organization, not for a stack trace, and the product already establishes the
intended behaviour (a unique, readable slug).

Both routes now use these functions. Concurrency is still handled at the commit
boundary by the callers (catch ``IntegrityError`` → 409), because a pre-flight
``SELECT`` cannot be atomic against a concurrent insert.
"""

from __future__ import annotations

import re

MAX_SLUG_LENGTH = 120


def generate_org_slug(company_name: str, max_length: int = MAX_SLUG_LENGTH) -> str:
    """Return a URL-safe slug for ``company_name`` (never empty)."""
    slug = (company_name or "").lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:max_length] or "org"


def ensure_unique_org_slug(base_slug: str, max_length: int = MAX_SLUG_LENGTH) -> str:
    """Append ``-1``, ``-2`` … until the slug is unused.

    Only a convenience for the non-racing case: the unique index added by
    ``r6b34_identity_integrity`` is the actual guarantee, and callers must still
    translate an ``IntegrityError`` at commit into a truthful response.
    """
    from app.models import Organization

    slug = (base_slug or "org")[:max_length]
    if Organization.query.filter_by(slug=slug).first() is None:
        return slug

    counter = 1
    while True:
        suffix = f"-{counter}"
        candidate = f"{slug[:max_length - len(suffix)]}{suffix}"
        if Organization.query.filter_by(slug=candidate).first() is None:
            return candidate
        counter += 1
