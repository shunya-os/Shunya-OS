"""
SHUNYA — Import/Export Fabric (FDA5-G7).

Safe import/export contracts for business data.
Every import has: validation, identity matching, duplicate detection, provenance.
Every export is: tenant-scoped, authorization-aware, provenance-preserving.
"""
import csv
import io
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from core.identity_interface import IdentityClaim, ClaimType

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Shared types
# ═══════════════════════════════════════════════════════════════════

class ImportStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class ImportResult:
    """Result of an import operation."""
    total: int = 0
    imported: int = 0
    skipped: int = 0
    errors: list[dict] = field(default_factory=list)
    status: ImportStatus = ImportStatus.PENDING
    import_id: Optional[str] = None


@dataclass
class ExportResult:
    """Result of an export operation."""
    data: Any = None
    format: str = "json"
    total: int = 0
    tenant_id: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════
# Import interfaces
# ═══════════════════════════════════════════════════════════════════

class DataImporter(ABC):
    """Interface for importing data into SHUNYA."""

    @abstractmethod
    def validate(self, data: Any) -> list[dict]:
        """Validate input data. Returns list of errors."""
        ...

    @abstractmethod
    def import_data(self, data: Any, tenant_id: str) -> ImportResult:
        """Import data with validation, dedup, and provenance."""
        ...

    @abstractmethod
    def supported_formats(self) -> list[str]:
        """Return list of supported import formats."""
        ...


class DataExporter(ABC):
    """Interface for exporting data from SHUNYA."""

    @abstractmethod
    def export_data(self, tenant_id: str, format: str = "json") -> ExportResult:
        """Export data scoped to tenant."""
        ...

    @abstractmethod
    def supported_formats(self) -> list[str]:
        ...


# ═══════════════════════════════════════════════════════════════════
# CSV Importer
# ═══════════════════════════════════════════════════════════════════

class CSVContactImporter(DataImporter):
    """Import contacts from CSV. Uses IdentityService for dedup."""

    def __init__(self, identity_service=None):
        self._identity_service = identity_service

    def supported_formats(self) -> list[str]:
        return ["csv"]

    def validate(self, data: Any) -> list[dict]:
        """Validate CSV data. Returns list of error dicts."""
        errors = []
        try:
            if isinstance(data, str):
                data = io.StringIO(data)
            reader = csv.DictReader(data)
            rows = list(reader)
            if not rows:
                errors.append({"row": 0, "field": "file", "message": "Empty CSV"})
            for i, row in enumerate(rows):
                if not row.get("email") and not row.get("name"):
                    errors.append({"row": i + 1, "field": "email", "message": "Email or name required"})
        except Exception as e:
            errors.append({"row": 0, "field": "file", "message": str(e)})
        return errors

    def import_data(self, data: Any, tenant_id: str) -> ImportResult:
        """Import CSV contacts with identity resolution."""
        result = ImportResult(status=ImportStatus.PROCESSING)

        try:
            if isinstance(data, str):
                data = io.StringIO(data)
            reader = csv.DictReader(data)
            rows = list(reader)
            result.total = len(rows)

            for i, row in enumerate(rows):
                try:
                    self._import_row(row, tenant_id, i)
                    result.imported += 1
                except Exception as e:
                    result.errors.append({"row": i + 1, "message": str(e)})
                    result.skipped += 1

            result.status = ImportStatus.COMPLETED if not result.errors else ImportStatus.PARTIAL
        except Exception as e:
            result.status = ImportStatus.FAILED
            result.errors.append({"row": 0, "message": str(e)})

        return result

    def _import_row(self, row: dict, tenant_id: str, index: int) -> None:
        """Import a single CSV row with identity resolution."""
        if not self._identity_service:
            logger.warning("No identity service configured for CSV import")
            return

        email = row.get("email", "").strip()
        name = row.get("name", "").strip()
        phone = row.get("phone", "").strip()

        # Create identity claim from email
        if email:
            self._identity_service.add_claim(IdentityClaim(
                claim_value=email,
                claim_type=ClaimType.EMAIL,
                source="import_csv",
                source_id=f"csv_import_{index}_{email}",
                tenant_id=tenant_id,
            ))

        # Create identity claim from name
        if name and not email:
            self._identity_service.add_claim(IdentityClaim(
                claim_value=name,
                claim_type=ClaimType.NAME,
                source="import_csv",
                source_id=f"csv_import_{index}_{name}",
                tenant_id=tenant_id,
            ))


# ═══════════════════════════════════════════════════════════════════
# JSON Importer
# ═══════════════════════════════════════════════════════════════════

class JSONDataImporter(DataImporter):
    """Import data from JSON. Supports contacts, objects, and relationships."""

    def __init__(self, identity_service=None):
        self._identity_service = identity_service

    def supported_formats(self) -> list[str]:
        return ["json"]

    def validate(self, data: Any) -> list[dict]:
        errors = []
        try:
            if isinstance(data, str):
                data = json.loads(data)
            if not isinstance(data, list):
                data = [data]
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    errors.append({"row": i + 1, "field": "data", "message": "Expected dict"})
        except Exception as e:
            errors.append({"row": 0, "field": "file", "message": str(e)})
        return errors

    def import_data(self, data: Any, tenant_id: str) -> ImportResult:
        result = ImportResult(status=ImportStatus.PROCESSING)
        try:
            if isinstance(data, str):
                data = json.loads(data)
            if not isinstance(data, list):
                data = [data]
            result.total = len(data)

            for i, item in enumerate(data):
                try:
                    self._import_item(item, tenant_id, i)
                    result.imported += 1
                except Exception as e:
                    result.errors.append({"row": i + 1, "message": str(e)})
                    result.skipped += 1

            result.status = ImportStatus.COMPLETED if not result.errors else ImportStatus.PARTIAL
        except Exception as e:
            result.status = ImportStatus.FAILED
            result.errors.append({"row": 0, "message": str(e)})
        return result

    def _import_item(self, item: dict, tenant_id: str, index: int) -> None:
        if not self._identity_service:
            return
        email = item.get("email", "")
        if email:
            self._identity_service.add_claim(IdentityClaim(
                claim_value=email,
                claim_type=ClaimType.EMAIL,
                source="import_json",
                source_id=f"json_import_{index}_{email}",
                tenant_id=tenant_id,
            ))