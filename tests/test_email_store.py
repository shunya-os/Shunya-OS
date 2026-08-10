"""Tests for email storage layer — uses isolated temp store."""

import os
import tempfile

from backend.core.email import email_store
from backend.core.email.email_entity import EmailEntity


def _patch_store(tmp_path):
    """Point email_store to an isolated temp file for test isolation."""
    store_file = os.path.join(tmp_path, "email_store.json")
    email_store.STORE_PATH = store_file
    return store_file


def test_store_and_retrieve_email():
    with tempfile.TemporaryDirectory() as tmp:
        _patch_store(tmp)
        email = EmailEntity(
            id="1",
            thread_id="thread-1",
            from_email="test@gmail.com",
            to_email=["a@gmail.com"],
            subject="Test",
            date="2026-01-01",
            body="Test body",
            type="lead",
            intent="travel_inquiry",
        )

        email_store.save_email(email)

        data = email_store.get_all()
        assert len(data) == 1
        assert data[0]["thread_id"] == "thread-1"
        assert data[0]["type"] == "lead"
        assert data[0]["intent"] == "travel_inquiry"


def test_deduplicate_by_thread_id():
    """save_email() must dedup by thread_id — same thread updates, never duplicates."""
    with tempfile.TemporaryDirectory() as tmp:
        _patch_store(tmp)

        email1 = EmailEntity(
            id="1",
            thread_id="thread-1",
            from_email="test@gmail.com",
            to_email=["a@gmail.com"],
            subject="Original",
            date="2026-01-01",
            body="Original body",
            type="unknown",
            intent="unknown",
        )
        email2 = EmailEntity(
            id="2",
            thread_id="thread-1",
            from_email="test@gmail.com",
            to_email=["a@gmail.com"],
            subject="Updated",
            date="2026-01-02",
            body="Updated body",
            type="payment",
            intent="payment",
        )

        email_store.save_email(email1)
        email_store.save_email(email2)

        data = email_store.get_all()
        assert len(data) == 1, "Dedup must keep exactly 1 record per thread_id"
        assert data[0]["subject"] == "Updated"
        assert data[0]["type"] == "payment"
        assert data[0]["id"] == "2"


def test_deduplicate_preserves_unrelated_threads():
    """Different thread_ids both survive."""
    with tempfile.TemporaryDirectory() as tmp:
        _patch_store(tmp)

        email_store.save_email(
            EmailEntity(id="1", thread_id="thread-a", subject="A", from_email="a@a.com",
                        to_email=["b@b.com"], date=None, body="")
        )
        email_store.save_email(
            EmailEntity(id="2", thread_id="thread-b", subject="B", from_email="a@a.com",
                        to_email=["b@b.com"], date=None, body="")
        )

        data = email_store.get_all()
        assert len(data) == 2


def test_get_all_empty():
    with tempfile.TemporaryDirectory() as tmp:
        _patch_store(tmp)
        data = email_store.get_all()
        assert isinstance(data, list)
        assert len(data) == 0