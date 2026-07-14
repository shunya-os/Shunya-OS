"""
Schema/Structure understanding — profile tabular inputs.
"""
import csv
import io
import json
from collections import Counter
from typing import Any


class ColumnProfile:
    """Profile of a single column."""
    def __init__(self, name: str, values: list):
        self.name = name
        self.non_null = [v for v in values if v is not None and str(v).strip() != ""]
        self.null_count = len(values) - len(self.non_null)
        self.null_frequency = round(self.null_count / len(values), 4) if values else 0
        self.row_count = len(values)
        self.unique_count = len(set(str(v) for v in self.non_null))
        self.sample_values = list(dict.fromkeys(str(v) for v in self.non_null))[:5]
        self.primitive_type = self._infer_type(self.non_null)
        self.duplicate_frequency = round(1 - self.unique_count / max(len(self.non_null), 1), 4)

    def _infer_type(self, values: list) -> str:
        if not values:
            return "unknown"
        samples = [str(v) for v in values[:20]]
        if all(self._is_int(v) for v in samples):
            return "integer"
        if all(self._is_float(v) for v in samples):
            return "decimal"
        if any("@" in v for v in samples):
            return "email"
        if any(v.startswith("+") and len(v) > 7 for v in samples):
            return "phone"
        return "text"

    @staticmethod
    def _is_int(v: str) -> bool:
        try:
            int(v.strip())
            return True
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def _is_float(v: str) -> bool:
        try:
            float(v.strip())
            return True
        except (ValueError, AttributeError):
            return False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "null_count": self.null_count,
            "null_frequency": self.null_frequency,
            "row_count": self.row_count,
            "unique_count": self.unique_count,
            "sample_values": self.sample_values,
            "primitive_type": self.primitive_type,
            "duplicate_frequency": self.duplicate_frequency,
        }


class SchemaProfiler:
    """Profile tabular data to understand its structure.
    Supports CSV and XLSX through the same pipeline."""

    @staticmethod
    def detect_separator(content: str) -> str:
        lines = content.strip().split("\n")
        if not lines:
            return ","
        header = lines[0]
        for sep in [",", "\t", "|", ";"]:
            if sep in header:
                return sep
        return ","

    @staticmethod
    def parse_csv(content: str, separator: str = ",") -> tuple[list[str], list[dict]]:
        reader = csv.DictReader(io.StringIO(content), delimiter=separator)
        columns = reader.fieldnames or []
        rows = list(reader)
        return columns, rows

    @staticmethod
    def parse_xlsx(filepath: str) -> tuple[list[str], list[dict]]:
        """Parse XLSX workbook. Uses first worksheet by default."""
        import openpyxl
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb.active
        if ws is None:
            return [], []
        rows_iter = ws.iter_rows(values_only=True)
        header_row = next(rows_iter, None)
        if not header_row:
            return [], []
        columns = [str(h) if h is not None else f"col_{i}" for i, h in enumerate(header_row)]
        rows = []
        for row in rows_iter:
            rows.append({columns[i]: (str(v) if v is not None else "") for i, v in enumerate(row)})
        wb.close()
        return columns, rows

    def profile(self, content: str = "", separator: str = "",
                xlsx_path: str = "") -> dict:
        """Profile tabular data. Pass content for CSV, xlsx_path for XLSX."""
        if xlsx_path:
            columns, rows = self.parse_xlsx(xlsx_path)
        else:
            if not separator:
                separator = self.detect_separator(content)
            columns, rows = self.parse_csv(content, separator)
        profiles = {}
        for col in columns:
            values = [row.get(col, "") for row in rows]
            profiles[col] = ColumnProfile(col, values)

        return {
            "columns": columns,
            "row_count": len(rows),
            "column_count": len(columns),
            "profiles": {k: v.to_dict() for k, v in profiles.items()},
        }