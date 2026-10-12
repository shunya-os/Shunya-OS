"""ZG-03 — milestone validator PR-ref handling (CI infra fix).

Reproduction: every ``pull_request`` CI build failed the execution-integrity
step because ``check_git_state()`` compared the ephemeral PR merge ref
(refs/pull/<n>/merge, detached HEAD) against ``origin/main`` — a comparison
that can never be equal, blocking every PR even when the full test suite
passed (the required check could never go green).

The fix adapts the invariant for PR builds: the PR head commit (the merge
ref's second parent) is the pushed remote commit being certified; it is
compared exactly against ``origin/$GITHUB_HEAD_REF`` when that ref is
fetchable, and accepted by construction (with the SHA recorded) otherwise.
Anomalies still fail closed, and local/push runs keep the original
HEAD == origin/<branch> semantics.
"""
import importlib.util
import os
from pathlib import Path

_VALIDATOR_PATH = Path(__file__).resolve().parent.parent / "scripts" / "validate_milestone.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_milestone_mod", _VALIDATOR_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_check(monkeypatch, env, fake_sh):
    mod = _load_validator()
    monkeypatch.setattr(mod, "sh", fake_sh)
    # Hermetic: GitHub Actions sets GITHUB_EVENT_NAME/GITHUB_HEAD_REF in CI;
    # clear them so each case fully controls the environment it exercises.
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return mod.check_git_state()


def test_pr_ref_with_fetchable_head_branch_matches_exactly(monkeypatch):
    """origin/<head_ref> == HEAD^2 -> PASS (exact comparison)."""
    def fake_sh(cmd, check=False):
        if cmd == "git rev-parse HEAD":
            return "aaa111merge"
        if cmd == "git rev-parse HEAD^2 2>/dev/null":
            return "bbb222prhead"
        if cmd == "git rev-parse origin/zero-gap-03 2>/dev/null":
            return "bbb222prhead"
        if cmd == "git status --porcelain":
            return ""
        return ""

    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    res = _run_check(monkeypatch,
                     {"GITHUB_EVENT_NAME": "pull_request",
                      "GITHUB_HEAD_REF": "zero-gap-03"},
                     fake_sh)
    assert res["head_matches_remote"] is True
    assert res["remote_head"] == "bbb222prhead"


def test_pr_ref_head_branch_unfetched_accepts_by_construction(monkeypatch):
    """Head branch not fetched (shallow PR checkout) -> PASS with head SHA."""
    def fake_sh(cmd, check=False):
        if cmd == "git rev-parse HEAD":
            return "aaa111merge"
        if cmd == "git rev-parse HEAD^2 2>/dev/null":
            return "bbb222prhead"
        if cmd == "git rev-parse origin/zero-gap-03 2>/dev/null":
            return "origin/zero-gap-03"  # rev-parse echo: ref not resolvable
        if cmd == "git status --porcelain":
            return ""
        return ""

    res = _run_check(monkeypatch,
                     {"GITHUB_EVENT_NAME": "pull_request",
                      "GITHUB_HEAD_REF": "zero-gap-03"},
                     fake_sh)
    assert res["head_matches_remote"] is True
    assert res["remote_head"] == "bbb222prhead"


def test_pr_ref_head_compare_mismatch_fails_closed(monkeypatch):
    """origin/<head_ref> exists but differs from HEAD^2 -> FAIL (anomaly)."""
    def fake_sh(cmd, check=False):
        if cmd == "git rev-parse HEAD":
            return "aaa111merge"
        if cmd == "git rev-parse HEAD^2 2>/dev/null":
            return "bbb222prhead"
        if cmd == "git rev-parse origin/zero-gap-03 2>/dev/null":
            return "ccc333different"
        if cmd == "git status --porcelain":
            return ""
        return ""

    res = _run_check(monkeypatch,
                     {"GITHUB_EVENT_NAME": "pull_request",
                      "GITHUB_HEAD_REF": "zero-gap-03"},
                     fake_sh)
    assert res["head_matches_remote"] is False


def test_local_run_semantics_unchanged(monkeypatch):
    """Without the PR event env, HEAD == origin/<branch> is still required."""
    def fake_sh(cmd, check=False):
        if cmd == "git rev-parse HEAD":
            return "mastertip"
        if cmd == "git rev-parse --abbrev-ref HEAD":
            return "master"
        if cmd == "git rev-parse origin/master 2>/dev/null":
            return "mastertip"
        if cmd == "git status --porcelain":
            return ""
        return ""

    res = _run_check(monkeypatch, {}, fake_sh)
    assert res["head_matches_remote"] is True

    def fake_sh_behind(cmd, check=False):
        if cmd == "git rev-parse HEAD":
            return "localwork"
        if cmd == "git rev-parse --abbrev-ref HEAD":
            return "master"
        if cmd == "git rev-parse origin/master 2>/dev/null":
            return "mastertip"
        if cmd == "git status --porcelain":
            return ""
        return ""

    res = _run_check(monkeypatch, {}, fake_sh_behind)
    assert res["head_matches_remote"] is False  # unpushed work still fails locally
