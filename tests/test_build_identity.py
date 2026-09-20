"""Tests for the immutable build identity (app/build_identity.py).

The defect this guards: /health derived git_commit from mutable `git rev-parse
HEAD`, so a worker recycled after an un-deployed checkout change could report a
SHA that no immutable release corresponds to.
"""
from __future__ import annotations

import json

from app import build_identity as bi


def _with_file(monkeypatch, tmp_path, payload):
    path = tmp_path / "build_identity.json"
    if payload is not None:
        path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(bi, "BUILD_IDENTITY_FILE", str(path))
    return path


def test_missing_record_is_absent_not_invented(monkeypatch, tmp_path):
    _with_file(monkeypatch, tmp_path, None)
    assert bi.build_identity() is None
    # Absence is NOT a mismatch — it is a different condition from disagreement.
    assert bi.identity_mismatch("abc123", None) is False
    assert bi.identity_mismatch("abc123", bi.build_identity()) is False


def test_valid_record_is_read(monkeypatch, tmp_path):
    _with_file(monkeypatch, tmp_path, {
        "backend_release_sha": "a" * 40,
        "build_id": "aaaaaaa",
        "frontend_release_sha": "a" * 40,
    })
    ident = bi.build_identity()
    assert ident is not None
    assert ident["backend_release_sha"] == "a" * 40


def test_matching_build_is_not_a_mismatch(monkeypatch, tmp_path):
    _with_file(monkeypatch, tmp_path, {"backend_release_sha": "b" * 40})
    assert bi.identity_mismatch("b" * 40, bi.build_identity()) is False


def test_differing_build_is_a_mismatch(monkeypatch, tmp_path):
    """The loaded build does not correspond to the certified deployment."""
    _with_file(monkeypatch, tmp_path, {"backend_release_sha": "c" * 40})
    assert bi.identity_mismatch("d" * 40, bi.build_identity()) is True


def test_blank_values_are_not_a_mismatch(monkeypatch, tmp_path):
    _with_file(monkeypatch, tmp_path, {"backend_release_sha": ""})
    assert bi.identity_mismatch("e" * 40, bi.build_identity()) is False
    _with_file(monkeypatch, tmp_path, {"backend_release_sha": "f" * 40})
    assert bi.identity_mismatch("", bi.build_identity()) is False


def test_corrupt_record_fails_safe(monkeypatch, tmp_path):
    path = tmp_path / "build_identity.json"
    path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(bi, "BUILD_IDENTITY_FILE", str(path))
    assert bi.build_identity() is None
