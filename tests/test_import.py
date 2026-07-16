"""Tests for the data import engine."""
import pytest
from app.shunya.data_import import (
    parse_csv, parse_json, _fuzzy_match, inspect_data, ColumnMatch
)


class TestParsing:
    def test_parse_csv_basic(self):
        r = parse_csv("a,b\n1,2\n3,4")
        assert len(r) == 2
        assert r[0] == {"a": "1", "b": "2"}

    def test_parse_csv_empty(self):
        assert parse_csv("a\n\n") == []

    def test_parse_json_array(self):
        r = parse_json('[{"x":1},{"x":2}]')
        assert len(r) == 2

    def test_parse_json_single_dict(self):
        r = parse_json('{"name":"test"}')
        assert len(r) == 1
        assert r[0]["name"] == "test"

    def test_parse_json_nested(self):
        r = parse_json('{"data":[{"a":1}],"meta":"x"}')
        assert len(r) == 1
        assert r[0]["a"] == 1


class TestFuzzyMatch:
    def test_exact_match(self):
        m = _fuzzy_match("name", [{"name": "name", "label": "Name"}])
        assert m and m.confidence == 1.0 and m.field_name == "name"

    def test_label_match(self):
        m = _fuzzy_match("FullName", [{"name": "name", "label": "Full Name"}])
        assert m and m.field_name == "name" and m.confidence >= 0.9

    def test_substring_match(self):
        m = _fuzzy_match("email_address", [{"name": "email", "label": "Email"}])
        assert m and m.field_name == "email" and m.confidence >= 0.3  # Actual threshold

    def test_phone_variants(self):
        m = _fuzzy_match("phone_no", [{"name": "phone", "label": "Phone"}])
        assert m and m.field_name == "phone" and m.confidence >= 0.5

    def test_no_match(self):
        m = _fuzzy_match("randomcol", [{"name": "name", "label": "Name"}])
        assert m is None or m.confidence < 0.3


class TestInspect:
    def test_basic_inspection(self):
        schema = [{"name": "name", "label": "Name", "type": "text", "required": True}]
        data = [{"name": "Alice"}, {"name": "Bob"}]
        p = inspect_data(data, "lead", schema, "Lead")
        assert p.total_rows == 2
        assert p.entity_type == "lead"
        assert len(p.matched_columns) >= 1

    def test_unmatched_columns(self):
        schema = [{"name": "name", "label": "Name", "type": "text"}]
        data = [{"name": "Alice", "extra": "x"}]
        p = inspect_data(data, "lead", schema)
        assert "extra" in p.unmatched_columns

    def test_missing_required(self):
        schema = [{"name": "email", "label": "Email", "type": "email", "required": True}]
        data = [{"name": "Alice"}]
        p = inspect_data(data, "lead", schema)
        assert len(p.missing_required) > 0

    def test_sample_rows(self):
        schema = [{"name": "name", "label": "Name", "type": "text"}]
        data = [{"name": f"Person{i}"} for i in range(10)]
        p = inspect_data(data, "lead", schema)
        assert len(p.sample_rows) == 3


class TestIntegration:
    def test_import_creates_entities(self, app, db, tenant, lead_definition):
        from app.shunya.data_import import import_data
        from app.models import Entity
        rows = [{"name": "Test Lead", "email": "t@t.com"}]
        result = import_data(rows, "lead", lead_definition.schema,
                             tenant.id, lead_definition.id,
                             {"name": "name", "email": "email"},
                             1, db.session)  # Pass session, not db object
        assert result["imported"] >= 1
        assert result["entity_type"] == "lead"
        assert len(result["errors"]) == 0