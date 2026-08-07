"""Universal Personal Operating System — UCP-12.

The final UCP. The orchestration layer that continuously understands
reality, composes intelligence, and assists execution.

No dashboard. No chatbot. No CRM. No task manager.
The Personal OS determines everything automatically.
"""

from core.personal_os.orchestrator import PersonalOSOrchestrator
from core.personal_os.models import (
    AttentionSignal, ExecutableRecommendation, LivingContextSnapshot, MemoryRecord,
)
from core.personal_os.attention import AttentionEngine
from core.personal_os.memory import MemoryEngine
from core.personal_os.workspace import WorkspaceEngine
from core.personal_os.execution import ExecutionOrchestrator
from core.personal_os.providers import ProviderOrchestrator

__all__ = [
    "PersonalOSOrchestrator",
    "AttentionEngine", "MemoryEngine", "WorkspaceEngine",
    "ExecutionOrchestrator", "ProviderOrchestrator",
    "AttentionSignal", "ExecutableRecommendation",
    "LivingContextSnapshot", "MemoryRecord",
]