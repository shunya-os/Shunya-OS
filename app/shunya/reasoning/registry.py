"""SHUNYA — Reasoning Engine: Rule Registry (Phase F — Canonical).

Manages rule registration, versioning, ordering, enable/disable,
and independent execution of deterministic reasoning rules.

Architectural authority: G5.7 — Canonical Phase F Architecture Decision
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from app.shunya.reasoning.models import Contradiction, Finding


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass
class RuleResult:
    """The result of executing a single rule.

    A rule produces zero or more findings and contradictions.
    Rules do NOT generate plans, execute actions, invoke LLMs,
    produce prompts, or make autonomous decisions.
    """

    rule_name: str = ""
    rule_version: int = 1
    passed: bool = True
    findings: List[Finding] = field(default_factory=list)
    contradictions: List[Contradiction] = field(default_factory=list)
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


RuleFn = Callable[..., "RuleResult"]


@dataclass
class RuleDefinition:
    """A registered rule definition."""

    name: str
    version: int = 1
    priority: int = 100  # Lower = executed first
    enabled: bool = True
    description: str = ""
    category: str = ""  # "observation", "gap", "contradiction", "risk", "composite"
    fn: Optional[RuleFn] = None
    created_at: float = 0.0
    updated_at: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        now = time.time()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


# ---------------------------------------------------------------------------
# Rule Registry
# ---------------------------------------------------------------------------


class RuleRegistry:
    """Registry of reasoning rules."""

    def __init__(self) -> None:
        self._rules: Dict[str, RuleDefinition] = {}
        self._execution_order: List[str] = []

    # ---- Registration ------------------------------------------------------

    def register(self, rule: RuleDefinition) -> None:
        existing = self._rules.get(rule.name)
        if existing:
            rule.version = existing.version + 1
            rule.created_at = existing.created_at
        rule.updated_at = time.time()
        self._rules[rule.name] = rule
        self._rebuild_order()

    def unregister(self, name: str) -> bool:
        if name in self._rules:
            del self._rules[name]
            self._rebuild_order()
            return True
        return False

    def get(self, name: str) -> Optional[RuleDefinition]:
        return self._rules.get(name)

    def list_rules(self, category: Optional[str] = None,
                   enabled_only: bool = False) -> List[RuleDefinition]:
        rules = list(self._rules.values())
        if category:
            rules = [r for r in rules if r.category == category]
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return sorted(rules, key=lambda r: r.priority)

    # ---- Enable / Disable --------------------------------------------------

    def enable(self, name: str) -> bool:
        rule = self._rules.get(name)
        if rule:
            rule.enabled = True
            rule.updated_at = time.time()
            return True
        return False

    def disable(self, name: str) -> bool:
        rule = self._rules.get(name)
        if rule:
            rule.enabled = False
            rule.updated_at = time.time()
            return True
        return False

    def is_enabled(self, name: str) -> bool:
        rule = self._rules.get(name)
        return rule is not None and rule.enabled

    # ---- Execution ---------------------------------------------------------

    def execute_all(self, context: Any = None) -> List[RuleResult]:
        results: List[RuleResult] = []
        for rule in self.list_rules(enabled_only=True):
            result = self._execute_single(rule, context)
            results.append(result)
        return results

    def execute_category(self, category: str, context: Any = None) -> List[RuleResult]:
        results: List[RuleResult] = []
        for rule in self.list_rules(category=category, enabled_only=True):
            result = self._execute_single(rule, context)
            results.append(result)
        return results

    def execute_by_name(self, name: str, context: Any = None) -> Optional[RuleResult]:
        rule = self._rules.get(name)
        if rule is None or not rule.enabled:
            return None
        return self._execute_single(rule, context)

    def execute_multiple(self, names: List[str], context: Any = None) -> List[RuleResult]:
        results: List[RuleResult] = []
        for name in names:
            result = self.execute_by_name(name, context)
            if result:
                results.append(result)
        return results

    # ---- Internal ----------------------------------------------------------

    def _execute_single(self, rule: RuleDefinition, context: Any) -> RuleResult:
        start = time.time()
        try:
            if rule.fn is None:
                return RuleResult(rule_name=rule.name, rule_version=rule.version,
                                  passed=False, error="Rule has no executable function")
            result = rule.fn(context)
            if not isinstance(result, RuleResult):
                result = RuleResult(rule_name=rule.name, rule_version=rule.version,
                                    findings=[], contradictions=[])
            result.rule_name = rule.name
            result.rule_version = rule.version
            result.elapsed_ms = (time.time() - start) * 1000
            return result
        except Exception as e:
            return RuleResult(rule_name=rule.name, rule_version=rule.version,
                              passed=False, error=str(e),
                              elapsed_ms=(time.time() - start) * 1000)

    def _rebuild_order(self) -> None:
        self._execution_order = [r.name for r in sorted(
            self._rules.values(), key=lambda r: r.priority)]

    def clear(self) -> None:
        self._rules.clear()
        self._execution_order.clear()

    @property
    def count(self) -> int:
        return len(self._rules)

    @property
    def enabled_count(self) -> int:
        return sum(1 for r in self._rules.values() if r.enabled)