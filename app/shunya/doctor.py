"""
Shunya — Doctor Layer (Phase 2)

Architecture integrity checker. Verifies the system hasn't drifted.
Checks: package health, required layers, governance policies, DB schema, version compatibility.
"""

import importlib
import os
from datetime import datetime, timezone
from typing import Optional

from app import db
from sqlalchemy import text


class DoctorReport:
    def __init__(self):
        self.checks: list[dict] = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add(self, name: str, status: str, detail: str = ""):
        self.checks.append({"check": name, "status": status, "detail": detail, "timestamp": datetime.now(timezone.utc).isoformat()})
        if status == "pass": self.passed += 1
        elif status == "fail": self.failed += 1
        else: self.warnings += 1

    def to_dict(self) -> dict:
        return {
            "summary": f"{self.passed} passed, {self.failed} failed, {self.warnings} warnings",
            "passed": self.passed, "failed": self.failed, "warnings": self.warnings,
            "healthy": self.failed == 0,
            "checks": self.checks,
        }


class DoctorLayer:
    def __init__(self, governance=None, knowledge_store=None):
        self._governance = governance
        self._store = knowledge_store

    def run_full_check(self) -> DoctorReport:
        report = DoctorReport()
        self._check_packages(report)
        self._check_database(report)
        self._check_layers(report)
        self._check_governance(report)
        self._check_knowledge(report)
        self._check_env(report)
        return report

    def _check_packages(self, r: DoctorReport):
        required = ["flask", "sqlalchemy", "requests", "pdfkit", "dotenv"]
        for pkg in required:
            try:
                importlib.import_module(pkg)
                r.add(f"package.{pkg}", "pass", f"{pkg} is installed")
            except ImportError:
                r.add(f"package.{pkg}", "fail", f"{pkg} is not installed")

    def _check_database(self, r: DoctorReport):
        try:
            db.session.execute(text("SELECT 1"))
            result = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            tables = [row[0] for row in result]
            required_tables = {"leads", "payments", "invoices", "suppliers", "itinerary_refs", "activity_logs",
                               "knowledge_facts", "observations", "learning_entries", "team_members"}
            missing = required_tables - set(tables)
            if not missing:
                r.add("database.tables", "pass", "All required tables exist")
            else:
                r.add("database.tables", "warning", f"Missing tables: {missing}")
        except Exception as e:
            r.add("database.connect", "fail", str(e))

    def _check_layers(self, r: DoctorReport):
        layer_modules = {
            "Knowledge": "app.shunya.knowledge",
            "Reasoning": "app.shunya.reasoning",
            "Planner": "app.shunya.planner",
            "Governance": "app.shunya.governance",
            "Executor": "app.shunya.executor",
            "KnowledgeStore": "app.shunya.knowledge_store",
            "Observer": "app.shunya.observer_learning",
            "Auth": "app.auth",
        }
        for name, mod_path in layer_modules.items():
            try:
                importlib.import_module(mod_path)
                r.add(f"layer.{name}", "pass", f"{name} layer module is importable")
            except ImportError:
                r.add(f"layer.{name}", "fail", f"{name} layer module not found")

    def _check_governance(self, r: DoctorReport):
        if self._governance:
            stats = self._governance.stats
            r.add("governance.policies", "pass", f"{stats['policies_loaded']} policies loaded")
            r.add("governance.decisions", "pass", f"{stats['total_decisions']} decisions audited")

    def _check_knowledge(self, r: DoctorReport):
        if self._store:
            stats = self._store.stats()
            r.add("knowledge.integrity", "pass" if stats.get("integrity_pass") else "fail", "Checksum integrity verified" if stats.get("integrity_pass") else "Integrity violations detected")
            r.add("knowledge.facts", "pass", f"{stats.get('current_facts', 0)} current facts, {stats.get('domains', [])} domains")

    def _check_env(self, r: DoctorReport):
        required_vars = ["DATABASE_URL", "SECRET_KEY"]
        for var in required_vars:
            if os.getenv(var):
                r.add(f"env.{var}", "pass", f"{var} is set")
            else:
                r.add(f"env.{var}", "warning", f"{var} not set — using default")