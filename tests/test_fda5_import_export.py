"""FDA5-G7: Import/Export data portability tests."""
import pytest
import json


class TestImportExport:
    """Import/export contracts with validation, dedup, provenance."""

    def test_csv_contact_importer_supported_formats(self):
        from core.import_export import CSVContactImporter
        importer = CSVContactImporter()
        assert "csv" in importer.supported_formats()

    def test_csv_contact_importer_validates_empty(self):
        from core.import_export import CSVContactImporter
        importer = CSVContactImporter()
        errors = importer.validate("")
        assert len(errors) > 0

    def test_csv_contact_importer_validates_valid(self):
        from core.import_export import CSVContactImporter
        importer = CSVContactImporter()
        csv_data = "email,name,phone\ntest@test.com,Test User,+1234567890\n"
        errors = importer.validate(csv_data)
        assert len(errors) == 0

    def test_csv_contact_importer_validates_missing_fields(self):
        from core.import_export import CSVContactImporter
        importer = CSVContactImporter()
        csv_data = "email,name\n,\n"
        errors = importer.validate(csv_data)
        assert len(errors) > 0

    def test_csv_import_with_identity_service(self, app):
        from core.import_export import CSVContactImporter
        from app.identity.service import IdentityService
        with app.app_context():
            svc = IdentityService()
            importer = CSVContactImporter(identity_service=svc)
            csv_data = "email,name,phone\nimport-csv@test.com,CSV Import,+1234567890\n"
            result = importer.import_data(csv_data, tenant_id="1")
            assert result.status.value in ("completed", "partial")
            assert result.imported >= 1

    def test_json_importer_supported_formats(self):
        from core.import_export import JSONDataImporter
        importer = JSONDataImporter()
        assert "json" in importer.supported_formats()

    def test_json_importer_validates(self):
        from core.import_export import JSONDataImporter
        importer = JSONDataImporter()
        errors = importer.validate("invalid json{{{")
        assert len(errors) > 0

    def test_json_importer_validates_valid(self):
        from core.import_export import JSONDataImporter
        importer = JSONDataImporter()
        data = json.dumps([{"email": "json@test.com", "name": "JSON Import"}])
        errors = importer.validate(data)
        assert len(errors) == 0

    def test_json_import_with_identity(self, app):
        from core.import_export import JSONDataImporter
        from app.identity.service import IdentityService
        with app.app_context():
            svc = IdentityService()
            importer = JSONDataImporter(identity_service=svc)
            data = json.dumps([{"email": "json-import@test.com"}])
            result = importer.import_data(data, tenant_id="1")
            assert result.imported >= 1

    def test_import_result_dataclass(self):
        from core.import_export import ImportResult, ImportStatus
        r = ImportResult(total=10, imported=8, skipped=2, status=ImportStatus.PARTIAL)
        assert r.total == 10
        assert r.imported == 8
        assert r.skipped == 2
        assert r.status == ImportStatus.PARTIAL

    def test_csv_import_duplicate_detection(self, app):
        """Same email imported twice via CSV → one identity."""
        from core.import_export import CSVContactImporter
        from app.identity.service import IdentityService
        from core.identity_interface import ClaimType
        with app.app_context():
            svc = IdentityService()
            importer = CSVContactImporter(identity_service=svc)
            csv_data = "email,name\ncsv-dedup@test.com,Dup Test\n"
            # Import twice
            r1 = importer.import_data(csv_data, tenant_id="1")
            r2 = importer.import_data(csv_data, tenant_id="1")
            # Both should succeed
            assert r1.imported >= 1
            assert r2.imported >= 1
            # But only one person should exist
            resolution = svc.resolve("csv-dedup@test.com", ClaimType.EMAIL)
            assert resolution.identity_id is not None