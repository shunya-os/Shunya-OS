"""ZG-03 B3 — missing-schema migration parity, NUL-byte ingestion safety,
and provider error-classification generalization.

Network-free; runs against sqlite in-memory.
"""
import pytest


# ── 1. NUL-byte sanitization ────────────────────────────────────────────


class TestSanitizeText:

    def test_strips_nul_from_str(self):
        from app.common.text_safety import sanitize_text
        assert sanitize_text("ab\x00cd") == "abcd"
        assert "\x00" not in sanitize_text("\x00\x00")

    def test_strips_nul_from_bytes(self):
        from app.common.text_safety import sanitize_text
        assert sanitize_text(b"ab\x00cd") == "abcd"

    def test_none_becomes_empty(self):
        from app.common.text_safety import sanitize_text
        assert sanitize_text(None) == ""

    def test_plain_text_unchanged(self):
        from app.common.text_safety import sanitize_text
        assert sanitize_text("hello, world") == "hello, world"

    def test_dict_values_sanitized(self):
        from app.common.text_safety import sanitize_dict_values
        out = sanitize_dict_values({"a": "x\x00y", "b": 7, "c": None})
        assert out == {"a": "xy", "b": 7, "c": None}


class TestImportNulSanitization:
    """A CSV cell containing a NUL byte must not break the import — the value
    is persisted NUL-stripped (PostgreSQL rejects 0x00 in text)."""

    def _app(self):
        from app import create_app, db
        app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
            "DISABLE_RATE_LIMIT": True,
        })
        with app.app_context():
            from app.objects.legacy_models import Workspace, ShWorkspaceMembership, ShunyaObject  # noqa: F401
            db.create_all()
        return app, db

    def test_import_data_with_nul_cell(self):
        app, db = self._app()
        with app.app_context():
            from app.shunya.data_import import import_data
            from app.models import set_lead_tenant_id, clear_lead_tenant_id
            set_lead_tenant_id(1)  # canonical Entity creation requires tenant ctx
            try:
                rows = [
                    {"customer_name": "Bob\u0000Smith", "phone": "+91900\u0000123456",
                     "email": "bob@test.com", "notes": "nul\u0000inside"},
                ]
                report = import_data(rows)
                assert report["imported"] == 1, report
                from app.models import Lead
                lead = Lead.query.first()
                assert lead is not None
                assert lead.customer_name == "BobSmith"
                assert "\x00" not in (lead.customer_name or "")
                assert "\x00" not in (lead.phone or "")
                assert "\x00" not in (lead.notes or "")
            finally:
                clear_lead_tenant_id()
            db.session.remove()


# ── 2. Provider error-classification generalization ─────────────────────


class TestClassifyExceptionGeneralized:

    def test_status_carrying_exception_402(self):
        """huggingface_hub-style exception: carries response.status_code."""
        from app.ai.model_catalog import classify_exception

        class _Resp:
            status_code = 402

        class _Exc(RuntimeError):
            response = _Resp()

        assert classify_exception(_Exc("boom")).value == "CREDITS_REQUIRED"

    def test_message_only_402(self):
        from app.ai.model_catalog import classify_exception

        class _Exc(RuntimeError):
            pass

        err = _Exc("Client error '402 Payment Required' for url ... no remaining credits")
        assert classify_exception(err).value == "CREDITS_REQUIRED"

    def test_connect_error_network(self):
        from app.ai.model_catalog import classify_exception
        import httpx
        # Real httpx transport exceptions carry the names the classifier knows.
        assert classify_exception(httpx.ConnectTimeout("connect timeout")).value == "NETWORK_ERROR"
        assert classify_exception(httpx.RemoteProtocolError("reset")).value == "NETWORK_ERROR"

    def test_unknown_stays_unknown(self):
        from app.ai.model_catalog import classify_exception

        class _Odd(RuntimeError):
            pass

        assert classify_exception(_Odd("something weird")).value == "UNKNOWN"


# ── 3. Missing-schema migration parity (governance guard) ───────────────


class TestMissingSchemaMigration:
    """Every live model table found missing in production must be created by
    the migration chain (prevents model <-> migration drift recurrence)."""

    REQUIRED_TABLES = ("ai_execution_records", "user_profiles", "feedback_signals")

    def _migration_sources(self):
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[1]
        return list((root / "migrations" / "versions").glob("*.py"))

    @staticmethod
    def _migration_revision(text: str):
        import re
        m = re.search(r'^revision\s*=\s*"([^"]+)"', text, re.MULTILINE)
        return m.group(1) if m else None

    @staticmethod
    def _migration_down(text: str):
        import re
        m = re.search(r'^down_revision\s*=\s*"([^"]+)"', text, re.MULTILINE)
        return m.group(1) if m else None

    def test_tables_created_by_migration_chain(self):
        sources = "".join(p.read_text(encoding="utf-8") for p in self._migration_sources())
        for table in self.REQUIRED_TABLES:
            assert f'op.create_table("{table}"' in sources or f'op.create_table(\n            "{table}"' in sources, \
                f"migration chain must create {table}"

    def test_b3_migration_is_head(self):
        """The migration chain is single-headed and b3 chains off
        activity_logs_tenant.

        B3 locked the head at b3_missing_schema_tables; E1 (r6b29_alert_events)
        legitimately extends the chain. The invariant that matters is a
        single canonical head with no orphaned branches — updated to assert
        that, with the current head named explicitly.
        """
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[1]
        b3 = (root / "migrations" / "versions" / "b3_missing_schema_tables.py").read_text(encoding="utf-8")
        assert 'down_revision = "activity_logs_tenant"' in b3
        revisions = {}
        for p in self._migration_sources():
            text = p.read_text(encoding="utf-8")
            rev = self._migration_revision(text)
            down = self._migration_down(text)
            if rev:
                revisions[rev] = down
        heads = [r for r, d in revisions.items() if r not in revisions.values()]
        assert len(heads) == 1, f"expected single migration head, got {heads}"
        assert heads[0] == "r6b29_alert_events", f"canonical head is {heads[0]}"
        assert "b3_missing_schema_tables" in revisions

    def test_migration_is_idempotent_guarded(self):
        """The migration must guard with has_table so re-runs are no-ops."""
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[1]
        b3 = (root / "migrations" / "versions" / "b3_missing_schema_tables.py").read_text(encoding="utf-8")
        assert "has_table" in b3
        assert "def _table_exists" in b3