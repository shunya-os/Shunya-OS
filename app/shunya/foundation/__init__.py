"""Shunya Foundation — shared contracts, primitives, and result types.

This layer stays small and stable. It provides predictable primitives
that all other layers depend on. No business logic here.
"""
from typing import TypeVar, Generic, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

T = TypeVar("T")


class ShunyaError(Exception):
    """Base exception for all Shunya layer errors."""
    def __init__(self, message: str, code: str = "", details: Any = None):
        super().__init__(message)
        self.code = code or self.__class__.__name__
        self.details = details


class ValidationError(ShunyaError):
    """Input or state validation failed."""
    code = "VALIDATION_ERROR"


class PermissionError(ShunyaError):
    """Action not permitted by current authority."""
    code = "PERMISSION_DENIED"


class NotFoundError(ShunyaError):
    """Requested resource not found."""
    code = "NOT_FOUND"


class ConflictError(ShunyaError):
    """Request conflicts with current state."""
    code = "CONFLICT"


class GovernanceError(ShunyaError):
    """Action requires governance approval."""
    code = "NEEDS_GOVERNANCE"


@dataclass
class Result(Generic[T]):
    """Standard result wrapper for all layer operations."""
    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: str = ""
    governance_required: bool = False
    governance_level: str = "auto"
    next_action: Optional[dict] = None
    context: dict = field(default_factory=dict)

    @classmethod
    def ok(cls, data: T = None, **kwargs) -> "Result[T]":
        return cls(success=True, data=data, **kwargs)

    @classmethod
    def fail(cls, error: str, code: str = "", **kwargs) -> "Result[T]":
        return cls(success=False, error=error, error_code=code, **kwargs)

    @classmethod
    def needs_governance(cls, level: str = "govern", data: T = None,
                         message: str = "") -> "Result[T]":
        return cls(success=False, governance_required=True,
                   governance_level=level, error=message, data=data)


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class NextAction:
    """A contextual next-best-action recommendation."""
    title: str
    description: str
    action_type: str  # view, edit, create, approve, message, escalate
    target_url: str
    priority: Priority = Priority.MEDIUM
    reason: str = ""
    expected_outcome: str = ""
    confidence: float = 0.5
    role_required: str = "agent"
    entity_id: Optional[int] = None
    entity_type: str = ""