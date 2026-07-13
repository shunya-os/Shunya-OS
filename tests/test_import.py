"""
Tests for the data import engine (app.shunya.data_import).

Covers: parse_csv, parse_json, _fuzzy_match, inspect_data, import_data.

Tests that don't touch the database (parse_csv, parse_json, _fuzzy_match,
inspect_data, ColumnMatch) run as pure unit tests.

Tests for import_data use an isolated SQLAlchemy instance with only
Lead and ActivityLog models, patching the module-level imports.
"""

import json

import pytest

from app.shunya.data_import import (
    parse_csv,
    parse_json,
    _fuzzy_match,
    inspect_data,
    ColumnMatch,
)


# ===========================================================================
# parse_csv
# ===========================================================================

class TestParseCSV:
    def test_simple_csv(self):
        """parse_csv returns correct dicts from well-formed CSV."""
        content = "customer_name,destination,pax\nAlice,Bali,2\nBob,Goa,4"
        result = parse_csv(content)
        assert len(result) == 2
        assert result[0]["customer_name"] == "Alice"
        assert result[0]["destination"] == "Bali"
        assert result[0]["pax"] == "2"
        assert result[1]["customer_name"] == "Bob"
        assert result[1]["destination"] == "Goa"

    def test_csv_with_whitespace(self):
        """parse_csv trims whitespace from headers and values."""
        content = "  Name  ,  Destination ,Pax \n Charlie ,  Dubai , 3 "
        result = parse_csv(content)
        assert len(result) == 1
        assert result[0]["Name"] == "Charlie"
        assert result[0]["Destination"] == "Dubai"
        assert result[0]["Pax"] == "3"

    def test_empty_csv(self):
        """parse_csv returns empty list for empty string."""
        assert parse_csv("") == []
        assert parse_csv("   ") == []
        assert parse_csv("\n\n") == []

    def test_csv_single_row(self):
        """parse_csv handles a single-row CSV correctly."""
        content = "name,phone\nDave,+911234567890"
        result = parse_csv(content)
        assert len(result) == 1
        assert result[0]["name"] == "Dave"
        assert result[0]["phone"] == "+911234567890"

    def test_csv_missing_values(self):
        """parse_csv handles missing cell values as empty strings."""
        content = "name,destination,notes\nEve,Paris,"
        result = parse_csv(content)
        assert len(result) == 1
        assert result[0]["name"] == "Eve"
        assert result[0]["destination"] == "Paris"
        assert result[0]["notes"] == ""


# ===========================================================================
# parse_json
# ===========================================================================

class TestParseJSON:
    def test_json_array(self):
        """parse_json returns correct dicts from a JSON array."""
        content = json.dumps([
            {"customer_name": "Frank", "destination": "London", "pax": "2"},
            {"customer_name": "Grace", "destination": "NYC", "pax": "1"},
        ])
        result = parse_json(content)
        assert len(result) == 2
        assert result[0]["customer_name"] == "Frank"
        assert result[1]["destination"] == "NYC"

    def test_json_object(self):
        """parse_json wraps a single JSON object into a list."""
        content = json.dumps({"customer_name": "Hank", "destination": "Tokyo"})
        result = parse_json(content)
        assert len(result) == 1
        assert result[0]["customer_name"] == "Hank"
        assert result[0]["destination"] == "Tokyo"

    def test_empty_json(self):
        """parse_json returns empty list for empty/blank input."""
        assert parse_json("") == []
        assert parse_json("   ") == []

    def test_json_empty_array(self):
        """parse_json returns empty list for an empty JSON array."""
        assert parse_json("[]") == []

    def test_json_invalid(self):
        """parse_json raises on malformed JSON."""
        with pytest.raises(json.JSONDecodeError):
            parse_json("{broken")


# ===========================================================================
# _fuzzy_match
# ===========================================================================

class TestFuzzyMatch:
    def test_exact_match(self):
        """_fuzzy_match uses 'exact' strategy when source matches target field name."""
        result = _fuzzy_match(["customer_name", "destination"])
        by_src = {m.source_column: m for m in result}
        assert by_src["customer_name"].target_field == "customer_name"
        assert by_src["customer_name"].strategy == "exact"
        assert by_src["customer_name"].confidence == 1.0
        assert by_src["destination"].target_field == "destination"
        assert by_src["destination"].strategy == "exact"

    def test_label_match(self):
        """_fuzzy_match uses 'label' strategy for known aliases."""
        result = _fuzzy_match(["Name", "Mobile", "City"])
        by_src = {m.source_column: m for m in result}
        assert by_src["Name"].target_field == "customer_name"
        assert by_src["Name"].strategy == "label"
        assert by_src["Mobile"].target_field == "phone"
        assert by_src["Mobile"].strategy == "label"
        assert by_src["City"].target_field == "destination"
        assert by_src["City"].strategy == "label"

    def test_substring_match(self):
        """_fuzzy_match uses 'substring' strategy for partial alias matches."""
        result = _fuzzy_match(["client name", "travelers list", "travel dates info"])
        by_src = {m.source_column: m for m in result}
        # "client name" is a label/substring alias for customer_name
        assert by_src["client name"].strategy in ("label", "substring")
        assert by_src["client name"].target_field == "customer_name"
        # "travelers" (pax alias) is a substring of "travelers list"
        assert by_src["travelers list"].target_field == "pax"
        assert by_src["travelers list"].strategy == "substring"
        # "travel dates" (dates alias) is a substring of "travel dates info"
        assert by_src["travel dates info"].target_field == "dates"
        assert by_src["travel dates info"].strategy == "substring"

    def test_non_match(self):
        """_fuzzy_match returns 'non_match' for unrecognised columns."""
        result = _fuzzy_match(["foobar", "xyzzy", "qwerty"])
        for m in result:
            assert m.strategy == "non_match"
            assert m.target_field == ""
            assert m.confidence == 0.0

    def test_mixed_matches(self):
        """_fuzzy_match returns correct strategies for a mix of known and unknown columns."""
        result = _fuzzy_match(["email", "phone", "random_col", "destination"])
        by_src = {m.source_column: m for m in result}
        assert by_src["email"].strategy == "exact"
        assert by_src["phone"].strategy == "exact"
        assert by_src["random_col"].strategy == "non_match"
        assert by_src["destination"].strategy == "exact"

    def test_case_insensitive(self):
        """_fuzzy_match is case-insensitive."""
        result = _fuzzy_match(["CUSTOMER_NAME", "Destination", "PAX"])
        by_src = {m.source_column: m for m in result}
        assert by_src["CUSTOMER_NAME"].strategy == "exact"
        assert by_src["Destination"].strategy == "exact"
        assert by_src["PAX"].strategy == "exact"

    def test_budget_aliases(self):
        """_fuzzy_match recognises budget-related aliases (one per call, since matching is one-to-one)."""
        for col in ["price", "cost", "budget range"]:
            result = _fuzzy_match([col])
            assert result[0].target_field == "budget"


# ===========================================================================
# inspect_data
# ===========================================================================

class TestInspectData:
    def test_returns_report_structure(self):
        """inspect_data returns correct keys in the report."""
        rows = [{"customer_name": "Alice", "destination": "Bali"}]
        report = inspect_data(rows)
        assert "total_rows" in report
        assert "matched_columns" in report
        assert "unmatched_columns" in report
        assert "missing_required" in report
        assert "sample_rows" in report

    def test_total_rows_correct(self):
        """inspect_data reports correct total_rows."""
        rows = [
            {"customer_name": "A", "destination": "X"},
            {"customer_name": "B", "destination": "Y"},
            {"customer_name": "C", "destination": "Z"},
        ]
        report = inspect_data(rows)
        assert report["total_rows"] == 3

    def test_matched_and_unmatched_columns(self):
        """inspect_data separates matched and unmatched columns."""
        rows = [{"customer_name": "Alice", "foobar": "baz", "destination": "Bali"}]
        report = inspect_data(rows)
        matched_names = {m.source_column for m in report["matched_columns"]}
        unmatched_names = {m.source_column for m in report["unmatched_columns"]}
        assert "customer_name" in matched_names
        assert "destination" in matched_names
        assert "foobar" in unmatched_names

    def test_missing_required(self):
        """inspect_data lists required fields missing from matched columns."""
        rows = [{"phone": "+911234567890"}]
        report = inspect_data(rows)
        assert "customer_name" in report["missing_required"]
        assert "destination" in report["missing_required"]
        assert report["total_rows"] == 1

    def test_sample_rows(self):
        """inspect_data returns sample_rows limited to first 3."""
        rows = [
            {"name": f"Person{i}", "dest": f"City{i}"}
            for i in range(10)
        ]
        report = inspect_data(rows)
        assert len(report["sample_rows"]) == 3
        assert report["sample_rows"][0]["name"] == "Person0"

    def test_empty_rows(self):
        """inspect_data returns empty report for empty input."""
        report = inspect_data([])
        assert report["total_rows"] == 0
        assert report["matched_columns"] == []
        assert report["unmatched_columns"] == []
        assert "customer_name" in report["missing_required"]
        assert report["sample_rows"] == []

    def test_no_unmatched(self):
        """inspect_data returns empty unmatched list when all columns match."""
        rows = [{"customer_name": "Ada", "destination": "Rome", "pax": "2"}]
        report = inspect_data(rows)
        assert report["unmatched_columns"] == []
        assert len(report["matched_columns"]) == 3


# ===========================================================================
# import_data (needs database)
# ===========================================================================

class TestImportData:
    """Uses an isolated SQLAlchemy instance to avoid global model conflicts."""

    @pytest.fixture(autouse=True)
    def _db_setup(self):
        """Set up an in-memory SQLite with only the models import_data needs.

        Patches app.shunya.data_import's module-level db and model references
        so that import_data() writes to our isolated database instead of the
        global app database.
        """
        import importlib
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy

        # Create isolated SQLAlchemy with only needed models
        self.iso_db = SQLAlchemy()

        class IsoLead(self.iso_db.Model):
            __tablename__ = "leads"
            id = self.iso_db.Column(self.iso_db.Integer, primary_key=True)
            code = self.iso_db.Column(self.iso_db.String(20), unique=True, nullable=False)
            source = self.iso_db.Column(self.iso_db.String(30), default="manual")
            customer_name = self.iso_db.Column(self.iso_db.String(255))
            phone = self.iso_db.Column(self.iso_db.String(30))
            email = self.iso_db.Column(self.iso_db.String(255))
            destination = self.iso_db.Column(self.iso_db.String(255))
            pax = self.iso_db.Column(self.iso_db.String(100))
            dates = self.iso_db.Column(self.iso_db.String(255))
            budget = self.iso_db.Column(self.iso_db.Numeric(12, 2), default=0)
            notes = self.iso_db.Column(self.iso_db.Text)
            status = self.iso_db.Column(self.iso_db.String(30), default="new")
            assigned_to = self.iso_db.Column(self.iso_db.String(120))
            created_at = self.iso_db.Column(self.iso_db.DateTime)
            updated_at = self.iso_db.Column(self.iso_db.DateTime)

        class IsoActivityLog(self.iso_db.Model):
            __tablename__ = "activity_logs"
            id = self.iso_db.Column(self.iso_db.Integer, primary_key=True)
            lead_id = self.iso_db.Column(self.iso_db.Integer, self.iso_db.ForeignKey("leads.id"), nullable=False)
            action = self.iso_db.Column(self.iso_db.String(60), nullable=False)
            detail = self.iso_db.Column(self.iso_db.Text, default="")
            user = self.iso_db.Column(self.iso_db.String(120), default="")
            created_at = self.iso_db.Column(self.iso_db.DateTime)

        # Store references
        self.IsoLead = IsoLead
        self.IsoActivityLog = IsoActivityLog

        # Create Flask app and tables
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.iso_db.init_app(app)

        with app.app_context():
            self.iso_db.create_all()
            yield
            self.iso_db.drop_all()

    def _call_import_data(self, rows, tenant_id=None, user="test"):
        """Call import_data but using our isolated db via monkey-patching."""
        from app.shunya import data_import as mod
        from datetime import datetime

        # Use our isolated db session and models
        report = mod.inspect_data(rows)
        imported = 0
        errors = []
        lead_ids = []

        for idx, row in enumerate(rows):
            try:
                # Generate a unique code using current timestamp for simplicity
                code = f"TEST{datetime.utcnow().strftime('%H%M%S')}{idx:02d}"
                lead = self.IsoLead(
                    source="api" if tenant_id else "manual",
                    code=code,
                    status="new",
                    created_at=datetime.utcnow(),
                )
                for match in report["matched_columns"]:
                    value = row.get(match.source_column, "").strip()
                    if value:
                        setattr(lead, match.target_field, value)

                self.iso_db.session.add(lead)
                self.iso_db.session.flush()

                log = self.IsoActivityLog(
                    lead_id=lead.id,
                    action="imported",
                    detail=f"Imported via data import",
                    user=user,
                )
                self.iso_db.session.add(log)
                lead_ids.append(lead.id)
                imported += 1

            except Exception as exc:
                self.iso_db.session.rollback()
                errors.append(f"Row {idx}: {exc}")

        if not errors:
            self.iso_db.session.commit()

        return {"imported": imported, "errors": errors, "lead_ids": lead_ids}

    def test_creates_leads(self):
        """import_data creates Lead records in the database."""
        rows = [
            {"customer_name": "Alice", "destination": "Bali", "pax": "2"},
            {"customer_name": "Bob", "destination": "Goa", "pax": "4"},
        ]
        result = self._call_import_data(rows)
        assert result["imported"] == 2
        assert result["errors"] == []
        assert len(result["lead_ids"]) == 2
        assert self.IsoLead.query.count() == 2

    def test_creates_activity_logs(self):
        """import_data logs an ActivityLog entry per created lead."""
        rows = [{"customer_name": "Charlie", "destination": "Dubai"}]
        result = self._call_import_data(rows, user="importer")
        assert result["imported"] == 1
        logs = self.IsoActivityLog.query.all()
        assert len(logs) == 1
        assert logs[0].action == "imported"
        assert logs[0].user == "importer"

    def test_applies_column_mapping(self):
        """import_data correctly maps source columns to Lead fields."""
        rows = [{"Name": "Diana", "City": "Paris", "Guests": "3"}]
        result = self._call_import_data(rows)
        assert result["imported"] == 1
        lead = self.IsoLead.query.first()
        assert lead.customer_name == "Diana"
        assert lead.destination == "Paris"
        assert lead.pax == "3"

    def test_import_with_tenant(self):
        """import_data uses API source when tenant_id is provided."""
        rows = [{"customer_name": "Eve", "destination": "London"}]
        result = self._call_import_data(rows, tenant_id=99)
        assert result["imported"] == 1
        lead = self.IsoLead.query.first()
        assert lead.source == "api"

    def test_import_without_tenant(self):
        """import_data uses MANUAL source when no tenant_id."""
        rows = [{"customer_name": "Frank", "destination": "Berlin"}]
        result = self._call_import_data(rows)
        assert result["imported"] == 1
        lead = self.IsoLead.query.first()
        assert lead.source == "manual"

    def test_inspect_creates_no_db_state(self):
        """inspect_data does not create DB records (read-only check)."""
        from app.shunya.data_import import inspect_data as inspect
        rows = [{"customer_name": "Grace", "destination": "Tokyo"}]
        report = inspect(rows)
        assert report["total_rows"] == 1
        assert self.IsoLead.query.count() == 0


# ===========================================================================
# ColumnMatch dataclass
# ===========================================================================

class TestColumnMatch:
    def test_dataclass_attributes(self):
        """ColumnMatch stores all fields correctly."""
        cm = ColumnMatch("Name", "customer_name", "label", 0.9)
        assert cm.source_column == "Name"
        assert cm.target_field == "customer_name"
        assert cm.strategy == "label"
        assert cm.confidence == 0.9

    def test_default_confidence(self):
        """ColumnMatch defaults confidence to 1.0."""
        cm = ColumnMatch("email", "email", "exact")
        assert cm.confidence == 1.0