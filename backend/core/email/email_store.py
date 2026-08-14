import os, json
STORE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "email_store.json")
"""
[DEPRECATED] Development-only JSON file store.
Production email persistence uses the PostgreSQL-backed canonical GmailAdapter pathway.
This module must not become a second production memory authority.
"""
import warnings
warnings.warn(
    "email_store.py is a development-only JSON store. Production email uses GmailAdapter (PostgreSQL).",
    DeprecationWarning, stacklevel=2,
)

def save_email(entity):
    """[DEPRECATED] Save email to JSON file. Use GmailAdapter.ingest_emails() instead."""
    import json, os, warnings
    warnings.warn("email_store.save_email is deprecated for production use", DeprecationWarning, stacklevel=2)
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    data = []
    if os.path.exists(STORE_PATH):
        try:
            with open(STORE_PATH, "r") as f:
                data = json.load(f)
        except Exception:
            pass
    existing = next((e for e in data if e.get("thread_id") == entity.thread_id), None)
    if existing:
        existing.update(entity.__dict__)
    else:
        data.append(entity.__dict__)
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def get_all():
    """[DEPRECATED] Get all emails from JSON store."""
    if not os.path.exists(STORE_PATH):
        return []
    with open(STORE_PATH, "r") as f:
        return json.load(f)
