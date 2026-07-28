"""
SHUNYA Object Registry — Type Registry and Protocol Compliance.

The ObjectRegistry manages type registration, object discovery,
type hierarchy, and protocol compliance verification. The
ProtocolComplianceChecker validates that objects implement all 15
mandatory sections of the Universal Object Protocol.

Usage:
    from core.registry import ObjectRegistry, ProtocolComplianceChecker

    registry = ObjectRegistry()
    registry.register_type(str, type_name="my_type")
    registry.register_object("my_type", "obj_1", {"object_id": "obj_1"})

    checker = ProtocolComplianceChecker()
    report = checker.full_compliance_check(my_object)
    if report.compliant:
        print("Object is fully compliant!")
"""

from .engine import (
    ObjectRegistry,
    ProtocolComplianceChecker,
    TypeHierarchy,
    get_compliance_checker,
    reset_compliance_checker,
)
from .models import (
    ComplianceReport,
    ObjectMetadata,
    ObjectStatus,
    ProtocolSection,
)

__all__ = [
    # Registry
    "ObjectRegistry",
    "TypeHierarchy",
    # Protocol compliance
    "ProtocolComplianceChecker",
    "get_compliance_checker",
    "reset_compliance_checker",
    # Models
    "ComplianceReport",
    "ObjectMetadata",
    "ObjectStatus",
    "ProtocolSection",
]
