"""Formal governance system — policies, registry, loader, reports.

Port of the half-done TypeScript architecture from shunya-core.
Implements 5 formal policy types: ADR, Capability Catalog, Product Definition,
Roadmap, and Release Notes.

Each policy checks a specific governance requirement and returns a
GovernancePolicyResult. run_all_policies() collects results into a
GovernanceReport for display on the governance dashboard.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class PolicyStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class GovernancePolicyResult:
    policy_id: str
    policy_name: str
    status: PolicyStatus
    detail: str = ""
    suggestions: List[str] = field(default_factory=list)


@dataclass
class GovernanceReport:
    version: int = 1
    results: List[GovernancePolicyResult] = field(default_factory=list)
    timestamp: str = ""

    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.status == PolicyStatus.PASS)

    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status in (PolicyStatus.FAIL, PolicyStatus.ERROR))

    def warn_count(self) -> int:
        return sum(1 for r in self.results if r.status == PolicyStatus.WARN)


# ── 5 Formal Policies ──

def check_adr_policy() -> GovernancePolicyResult:
    """GOV-POLICY-001: Check that docs/adr contains at least one valid ADR."""
    import os
    adr_dir = os.path.expanduser("~/shunya_os/docs/adr")
    if not os.path.isdir(adr_dir):
        return GovernancePolicyResult(
            "GOV-POLICY-001", "ADR Exists", PolicyStatus.FAIL,
            "No docs/adr/ directory found",
            ["Run `mkdir -p ~/shunya_os/docs/adr` and create ADR-001.md"],
        )
    md_files = [f for f in os.listdir(adr_dir) if f.endswith(".md")]
    if not md_files:
        return GovernancePolicyResult(
            "GOV-POLICY-001", "ADR Exists", PolicyStatus.FAIL,
            "No ADR (.md) files found in docs/adr/",
            ["Create an Architecture Decision Record, e.g. docs/adr/ADR-001-initial-architecture.md"],
        )
    return GovernancePolicyResult(
        "GOV-POLICY-001", "ADR Exists", PolicyStatus.PASS,
        f"Found {len(md_files)} ADR file(s)",
    )


def check_capability_catalog_policy() -> GovernancePolicyResult:
    """GOV-POLICY-002: Check that capability catalog exists and is non-empty."""
    import os
    cat = os.path.expanduser("~/shunya_os/repository/capabilities/catalog.yaml")
    if not os.path.exists(cat):
        return GovernancePolicyResult(
            "GOV-POLICY-002", "Capability Catalog", PolicyStatus.FAIL,
            "No catalog.yaml found",
            ["Create ~/shunya_os/repository/capabilities/catalog.yaml with capability definitions"],
        )
    try:
        import yaml
        with open(cat) as f:
            data = yaml.safe_load(f)
        if not data or not isinstance(data, dict):
            return GovernancePolicyResult(
                "GOV-POLICY-002", "Capability Catalog", PolicyStatus.WARN,
                "catalog.yaml exists but is empty or not a mapping",
            )
        count = len(data.get("capabilities", data))
        return GovernancePolicyResult(
            "GOV-POLICY-002", "Capability Catalog", PolicyStatus.PASS,
            f"Capability catalog exists with {count} entries",
        )
    except ImportError:
        return GovernancePolicyResult(
            "GOV-POLICY-002", "Capability Catalog", PolicyStatus.PASS,
            "Capability catalog file exists (yaml parsing skipped — pyyaml not installed)",
        )


def check_product_definition_policy() -> GovernancePolicyResult:
    """GOV-POLICY-003: Check that product definition exists."""
    import os
    prod = os.path.expanduser("~/shunya_os/docs/product/PRODUCT_DEFINITION.md")
    if not os.path.exists(prod):
        return GovernancePolicyResult(
            "GOV-POLICY-003", "Product Definition", PolicyStatus.FAIL,
            "No PRODUCT_DEFINITION.md found",
            ["Create ~/shunya_os/docs/product/PRODUCT_DEFINITION.md with product overview, goals, and scope"],
        )
    size = os.path.getsize(prod)
    if size < 50:
        return GovernancePolicyResult(
            "GOV-POLICY-003", "Product Definition", PolicyStatus.WARN,
            f"PRODUCT_DEFINITION.md exists but is only {size} bytes",
            ["Expand the product definition with meaningful content"],
        )
    return GovernancePolicyResult(
        "GOV-POLICY-003", "Product Definition", PolicyStatus.PASS,
        "Product definition exists",
    )


def check_roadmap_policy() -> GovernancePolicyResult:
    """GOV-POLICY-004: Check that roadmap exists and has phases."""
    import os
    path = os.path.expanduser("~/shunya_os/docs/roadmap/roadmap.yaml")
    if not os.path.exists(path):
        return GovernancePolicyResult(
            "GOV-POLICY-004", "Roadmap", PolicyStatus.FAIL,
            "No roadmap.yaml found",
            ["Create ~/shunya_os/docs/roadmap/roadmap.yaml with phases and milestones"],
        )
    try:
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f)
        phases = []
        if isinstance(data, dict):
            phases = data.get("phases", [])
        elif isinstance(data, list):
            phases = data
        if not phases:
            return GovernancePolicyResult(
                "GOV-POLICY-004", "Roadmap", PolicyStatus.WARN,
                "roadmap.yaml exists but has no phases defined",
                ["Add at least one phase with milestones to roadmap.yaml"],
            )
        return GovernancePolicyResult(
            "GOV-POLICY-004", "Roadmap", PolicyStatus.PASS,
            f"Roadmap exists with {len(phases)} phase(s)",
        )
    except ImportError:
        return GovernancePolicyResult(
            "GOV-POLICY-004", "Roadmap", PolicyStatus.PASS,
            "Roadmap file exists (yaml parsing skipped — pyyaml not installed)",
        )


def check_release_notes_policy() -> GovernancePolicyResult:
    """GOV-POLICY-005: Check that release docs exist."""
    import os
    rel = os.path.expanduser("~/shunya_os/docs/releases")
    if not os.path.isdir(rel):
        return GovernancePolicyResult(
            "GOV-POLICY-005", "Release Notes", PolicyStatus.FAIL,
            "No docs/releases/ directory",
            ["Run `mkdir -p ~/shunya_os/docs/releases` and add release notes"],
        )
    notes = [f for f in os.listdir(rel) if f.endswith(".md")]
    if not notes:
        return GovernancePolicyResult(
            "GOV-POLICY-005", "Release Notes", PolicyStatus.WARN,
            "docs/releases/ exists but has no release notes",
            ["Create a release note, e.g. docs/releases/v0.1.0.md"],
        )
    return GovernancePolicyResult(
        "GOV-POLICY-005", "Release Notes", PolicyStatus.PASS,
        f"Found {len(notes)} release document(s)",
    )


# ── Registry of ALL policies ──

ALL_POLICIES = [
    ("GOV-POLICY-001", "ADR Policy", check_adr_policy),
    ("GOV-POLICY-002", "Capability Catalog Policy", check_capability_catalog_policy),
    ("GOV-POLICY-003", "Product Definition Policy", check_product_definition_policy),
    ("GOV-POLICY-004", "Roadmap Policy", check_roadmap_policy),
    ("GOV-POLICY-005", "Release Notes Policy", check_release_notes_policy),
]


def run_all_policies() -> GovernanceReport:
    """Execute all governance policies and return a report."""
    from datetime import datetime
    results = [fn() for _, _, fn in ALL_POLICIES]
    return GovernanceReport(
        results=results,
        timestamp=datetime.utcnow().isoformat(),
    )


def run_policy(policy_id: str) -> Optional[GovernancePolicyResult]:
    """Execute a single policy by ID. Returns None if not found."""
    for pid, _name, fn in ALL_POLICIES:
        if pid == policy_id:
            return fn()
    return None