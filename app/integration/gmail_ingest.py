"""Real Gmail Ingestion Engine — fetches emails via Gmail API and converts to SHUNYA objects.

PHASE 3.5: Connects real Gmail data → identity resolution → object creation → decision pipeline.
Every email is traced through the full evidence → awareness → decision → execution pipeline.

Uses google-api-python-client with OAuth 2.0 tokens stored in the integration system.
"""

import base64
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── OAuth / API Client ────────────────────────────────────────────────────


def get_gmail_service(token_path: str = None):
    """Get an authenticated Gmail API service.

    Uses the stored OAuth token from integration_accounts or a token file.
    Falls back to GOOGLE_TOKEN_FILE env var.

    Args:
        token_path: Path to stored credentials JSON.

    Returns:
        googleapiclient.discovery.Resource or None
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        logger.error("google-api-python-client not installed. Run: pip install google-api-python-client google-auth-oauthlib")
        return None

    token_path = token_path or os.environ.get("GOOGLE_TOKEN_FILE")
    if not token_path or not os.path.exists(token_path):
        logger.warning("No Google token file found at %s. Run Gmail OAuth flow first.", token_path)
        return None

    try:
        creds = Credentials.from_authorized_user_file(
            token_path,
            ["https://www.googleapis.com/auth/gmail.readonly",
             "https://www.googleapis.com/auth/contacts.readonly",
             "https://www.googleapis.com/auth/calendar"]
        )
        if not creds or not creds.valid:
            logger.warning("Gmail credentials expired or invalid")
            return None
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        logger.error("Failed to create Gmail service: %s", e)
        return None


# ── Email Fetching ────────────────────────────────────────────────────────


def fetch_emails(max_results: int = 100, query: str = "newer_than:30d") -> list:
    """Fetch recent emails from Gmail inbox.

    Args:
        max_results: Maximum emails to fetch (default 100).
        query: Gmail search query (default: last 30 days).

    Returns:
        List of email dicts with: id, thread_id, sender, subject, body, timestamp, snippet.
    """
    service = get_gmail_service()
    if not service:
        logger.warning("Gmail service not available — cannot fetch emails")
        return []

    emails = []

    try:
        # List messages
        response = service.users().messages().list(
            userId="me", q=query, maxResults=min(max_results, 500)
        ).execute()

        messages = response.get("messages", [])
        logger.info("Fetched %d message IDs from Gmail", len(messages))

        for msg_ref in messages:
            try:
                msg = service.users().messages().get(
                    userId="me", id=msg_ref["id"], format="full"
                ).execute()

                email = _extract_email_data(msg)
                if email:
                    emails.append(email)
            except Exception as e:
                logger.warning("Failed to fetch message %s: %s", msg_ref.get("id"), e)

        logger.info("Successfully extracted %d/%d emails", len(emails), len(messages))

    except Exception as e:
        logger.error("Gmail API call failed: %s", e)

    return emails


def _extract_email_data(msg: dict) -> Optional[dict]:
    """Extract structured email data from a Gmail API message object."""
    try:
        msg_id = msg.get("id", "")
        thread_id = msg.get("threadId", "")
        payload = msg.get("payload", {})
        headers = {h.get("name", "").lower(): h.get("value", "") for h in payload.get("headers", [])}

        # Extract body
        body = _extract_body(payload)

        # Parse timestamp
        internal_date = msg.get("internalDate", "")
        timestamp = None
        if internal_date:
            try:
                timestamp = datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc)
            except (ValueError, OSError):
                timestamp = datetime.now(timezone.utc)

        sender_raw = headers.get("from", "unknown@unknown.com")
        sender_name = sender_raw.split("<")[0].strip() if "<" in sender_raw else sender_raw
        sender_email = sender_raw.split("<")[1].replace(">", "").strip() if "<" in sender_raw else sender_raw

        return {
            "id": msg_id,
            "thread_id": thread_id,
            "sender_raw": sender_raw,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": headers.get("subject", "(no subject)"),
            "body": body[:5000],  # Truncate very long bodies
            "snippet": msg.get("snippet", ""),
            "timestamp": timestamp.isoformat() if timestamp else None,
            "label_ids": msg.get("labelIds", []),
        }
    except Exception as e:
        logger.warning("Failed to extract email data: %s", e)
        return None


def _extract_body(payload: dict) -> str:
    """Recursively extract body text from a Gmail payload."""
    body = ""

    # Top-level body
    body_data = payload.get("body", {}).get("data", "")
    if body_data:
        try:
            body = base64.urlsafe_b64decode(body_data + "===").decode("utf-8", errors="replace")
        except Exception:
            pass

    # Check parts
    if not body:
        parts = payload.get("parts", [])
        for part in parts:
            part_data = part.get("body", {}).get("data", "")
            if part_data:
                try:
                    body = base64.urlsafe_b64decode(part_data + "===").decode("utf-8", errors="replace")
                    break
                except Exception:
                    continue

            # Recurse into sub-parts
            if part.get("parts"):
                body = _extract_body(part)
                if body:
                    break

    return body


# ── Email → Object Conversion ─────────────────────────────────────────────


def email_to_object(email_data: dict, source: str = "gmail") -> dict:
    """Convert an email into a SHUNYA object via identity resolution.

    Pipeline:
        1. Resolve sender identity (email → Object)
        2. Create or update the Object with email context
        3. Record evidence for the email
        4. Create a conversation record

    Args:
        email_data: Email dict from fetch_emails()
        source: Source identifier for evidence tracking.

    Returns:
        dict with object_id, matched, confidence, evidence_id, trace_id.
    """
    from app.core.identity.resolver import resolve_identity
    from app.evidence.models_db import create_evidence

    result = {"email_id": email_data.get("id"), "object_id": None, "matched": False, "confidence": 0.0}

    # Stage 1: Identity resolution
    identity = resolve_identity(
        email=email_data.get("sender_email"),
        name=email_data.get("sender_name"),
        source="gmail",
        metadata={
            "last_email_subject": email_data.get("subject", "")[:200],
            "last_email_at": email_data.get("timestamp"),
        },
    )
    obj = identity["object"]
    result["object_id"] = obj.id
    result["matched"] = identity["matched"]
    result["confidence"] = identity["confidence"]

    # Stage 2: Create evidence for this email
    evidence = create_evidence(
        source_type="email",
        source_id=email_data.get("id", "unknown"),
        raw_reference={
            "from": email_data.get("sender_email"),
            "subject": email_data.get("subject", "")[:200],
            "snippet": email_data.get("snippet", "")[:300],
            "thread_id": email_data.get("thread_id"),
        },
    )
    result["evidence_id"] = evidence.id

    # Stage 3: Create conversation thread reference
    try:
        from app.communication.models import MessageProposal
        from app.core.db import get_session

        status = "inbound"
        conv_obj = MessageProposal(
            entity_id=obj.id,
            to=email_data.get("sender_email", "unknown@unknown.com"),
            message=email_data.get("snippet", "")[:500],
            status=status,
            context_source="gmail",
            entity_type="lead",
            entity_name=email_data.get("sender_name", "Unknown"),
            context_reason=f"Email received: {email_data.get('subject', '')[:100]}",
        )
        get_session().add(conv_obj)
    except Exception as e:
        logger.warning("Failed to create conversation record: %s", e)

    # Stage 4: Trigger SHUNYA decision pipeline (if entry point available)
    try:
        from app.runtime.entry import process_event

        pipeline_result = process_event(
            event_type="email_received",
            event_data={
                "id": obj.id,
                "entity_id": obj.id,
                "email_id": email_data.get("id"),
                "subject": email_data.get("subject", ""),
                "sender": email_data.get("sender_email"),
                "source": "gmail",
            },
            source="gmail",
        )
        result["trace_id"] = pipeline_result.get("decision_trace_id")
        result["pipeline_status"] = pipeline_result.get("status")
        logger.info(
            "Email processed through pipeline: %s -> object #%d trace=%s",
            email_data.get("subject", "")[:50], obj.id, result.get("trace_id"),
        )
    except Exception as e:
        logger.warning("Decision pipeline failed for email %s: %s", email_data.get("id"), e)
        result["pipeline_status"] = "failed"

    return result


def ingest_emails(max_results: int = 100) -> dict:
    """Fetch and ingest the last N emails into SHUNYA.

    Returns:
        dict with:
            emails_fetched: int
            objects_created: int
            objects_matched: int
            traces_recorded: int
            errors: list
    """
    summary = {"emails_fetched": 0, "objects_created": 0, "objects_matched": 0, "traces_recorded": 0, "errors": []}

    emails = fetch_emails(max_results=max_results)
    summary["emails_fetched"] = len(emails)

    for email_data in emails:
        try:
            result = email_to_object(email_data, source="gmail")
            if result.get("matched"):
                summary["objects_matched"] += 1
            else:
                summary["objects_created"] += 1
            if result.get("trace_id"):
                summary["traces_recorded"] += 1
        except Exception as e:
            summary["errors"].append({"email_id": email_data.get("id"), "error": str(e)})

    logger.info(
        "Gmail ingestion: %d emails, %d new objects, %d matched, %d traces, %d errors",
        summary["emails_fetched"], summary["objects_created"],
        summary["objects_matched"], summary["traces_recorded"],
        len(summary["errors"]),
    )

    return summary


# ── Thread Linking ─────────────────────────────────────────────────────────


def link_threads(emails: list) -> dict:
    """Group emails by thread and return thread summaries.

    Each thread links conversations creating a coherent memory.
    """
    threads = {}
    for email in emails:
        tid = email.get("thread_id", "unknown")
        if tid not in threads:
            threads[tid] = {
                "thread_id": tid,
                "subject": email.get("subject", ""),
                "participants": set(),
                "message_count": 0,
                "first_message": email.get("timestamp"),
                "last_message": email.get("timestamp"),
                "messages": [],
            }
        t = threads[tid]
        t["message_count"] += 1
        t["participants"].add(email.get("sender_email"))
        if email.get("timestamp"):
            if not t["first_message"] or email["timestamp"] < t["first_message"]:
                t["first_message"] = email["timestamp"]
            if not t["last_message"] or email["timestamp"] > t["last_message"]:
                t["last_message"] = email["timestamp"]
        t["messages"].append({
            "id": email.get("id"),
            "sender": email.get("sender_email"),
            "snippet": (email.get("snippet") or "")[:100],
            "timestamp": email.get("timestamp"),
        })

    # Convert sets to lists for JSON serialization
    for tid in threads:
        threads[tid]["participants"] = list(threads[tid]["participants"])
        # Keep only last 5 messages per thread
        threads[tid]["messages"] = threads[tid]["messages"][-5:]

    return threads