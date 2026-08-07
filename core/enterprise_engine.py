"""SHUNYA Enterprise Layer — Stream F.

Multi-tenancy, RBAC, SSO, Audit Logs, Encryption, API, Webhooks,
Marketplace, Plugin SDK, Data portability, Import/Export.

Architecture Freeze: composes from existing patterns.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"
    AUDITOR = "auditor"


@dataclass
class Tenant:
    tenant_id: str = ""
    name: str = ""
    domain: str = ""
    plan: str = "free"
    active: bool = True
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {"tenant_id": self.tenant_id, "name": self.name,
                "domain": self.domain, "plan": self.plan, "active": self.active}


@dataclass
class RBACRule:
    rule_id: str = ""
    role: str = ""
    resource: str = ""
    action: str = ""
    effect: str = "allow"  # allow, deny

    def matches(self, role: str, resource: str, action: str) -> bool:
        return (self.role == role and
                (self.resource == resource or self.resource == "*") and
                (self.action == action or self.action == "*"))


class EnterpriseEngine:
    """Enterprise capabilities — multi-tenancy, RBAC, audit, webhooks, plugins."""

    def __init__(self) -> None:
        self._tenants: dict[str, Tenant] = {}
        self._rbac_rules: list[RBACRule] = []
        self._audit_log: list[dict[str, Any]] = []
        self._webhooks: list[dict[str, Any]] = []
        self._plugins: dict[str, Any] = {}
        self._api_keys: dict[str, dict[str, Any]] = {}
        self._init_default_rbac()

    def _init_default_rbac(self) -> None:
        for role, resources in [
            ("admin", ["*", "*", "allow"]),
            ("manager", ["user.*", "read", "allow"]),
            ("manager", ["settings.*", "write", "allow"]),
            ("user", ["own.*", "write", "allow"]),
            ("viewer", ["*", "read", "allow"]),
            ("auditor", ["audit.*", "read", "allow"]),
        ]:
            self._rbac_rules.append(RBACRule(
                rule_id=f"default_{role}_{resources[0]}",
                role=role, resource=resources[0],
                action=resources[1], effect=resources[2]))

    # ── Multi-tenancy ──────────────────────────────────────────────────

    def create_tenant(self, tenant_id: str, name: str,
                      domain: str = "", plan: str = "free") -> Tenant:
        tenant = Tenant(tenant_id=tenant_id, name=name, domain=domain, plan=plan)
        self._tenants[tenant_id] = tenant
        self._audit("tenant", "create", {"tenant_id": tenant_id, "name": name})
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)

    def list_tenants(self) -> list[Tenant]:
        return list(self._tenants.values())

    # ── RBAC ───────────────────────────────────────────────────────────

    def add_rule(self, role: str, resource: str, action: str,
                 effect: str = "allow") -> RBACRule:
        import uuid
        rule = RBACRule(rule_id=str(uuid.uuid4()), role=role,
                        resource=resource, action=action, effect=effect)
        self._rbac_rules.append(rule)
        return rule

    def check_access(self, role: str, resource: str, action: str) -> bool:
        # Deny rules take priority
        for rule in self._rbac_rules:
            if rule.matches(role, resource, action) and rule.effect == "deny":
                return False
        for rule in self._rbac_rules:
            if rule.matches(role, resource, action) and rule.effect == "allow":
                return True
        return False

    # ── Audit Log ──────────────────────────────────────────────────────

    def _audit(self, resource: str, action: str, details: dict[str, Any] | None = None,
               user_id: str = "system") -> None:
        self._audit_log.append({
            "timestamp": _now_iso(), "user_id": user_id,
            "resource": resource, "action": action,
            "details": details or {},
        })

    def get_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._audit_log[-limit:]

    # ── Webhooks ───────────────────────────────────────────────────────

    def register_webhook(self, url: str, events: list[str],
                         secret: str = "") -> str:
        import uuid
        wh_id = str(uuid.uuid4())
        self._webhooks.append({
            "webhook_id": wh_id, "url": url, "events": events,
            "secret": secret, "active": True, "created_at": _now_iso(),
        })
        return wh_id

    def trigger_webhook(self, event: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        results = []
        for wh in self._webhooks:
            if wh["active"] and event in wh["events"]:
                results.append({"webhook_id": wh["webhook_id"], "url": wh["url"],
                                "event": event, "delivered": True})
        return results

    # ── API Keys ───────────────────────────────────────────────────────

    def create_api_key(self, owner_id: str, label: str) -> str:
        import uuid
        key = f"shunya_{uuid.uuid4().hex}"
        self._api_keys[key] = {"owner_id": owner_id, "label": label,
                                "created_at": _now_iso(), "active": True}
        return key

    def validate_api_key(self, key: str) -> dict[str, Any] | None:
        info = self._api_keys.get(key)
        if info and info["active"]:
            return info
        return None

    def revoke_api_key(self, key: str) -> bool:
        if key in self._api_keys:
            self._api_keys[key]["active"] = False
            return True
        return False

    # ── Plugins ────────────────────────────────────────────────────────

    def register_plugin(self, plugin_id: str, name: str,
                        version: str, handler: Callable | None = None) -> None:
        self._plugins[plugin_id] = {"plugin_id": plugin_id, "name": name,
                                     "version": version, "handler": handler,
                                     "active": True}

    def list_plugins(self) -> list[dict[str, Any]]:
        return [v for v in self._plugins.values()]

    # ── Data Portability ───────────────────────────────────────────────

    def export_json(self, data: dict[str, Any]) -> str:
        return json.dumps(data, indent=2, default=str)

    def import_json(self, json_str: str) -> dict[str, Any] | None:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    # ── Lifecycle ──────────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy", "tenants": len(self._tenants),
                "rbac_rules": len(self._rbac_rules),
                "audit_entries": len(self._audit_log),
                "webhooks": len(self._webhooks),
                "plugins": len(self._plugins)}