"""Context Manager — prepares and summarises context for inference calls.

The context manager **never switches models for context window**.  If the
active model's context window is insufficient, the manager truncates or
summarises rather than routing to a different model.  This guarantees
that the model chosen by the policy engine is the one that actually serves
the request.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ── Public types ────────────────────────────────────────────────────────────


class TruncationStrategy(str, enum.Enum):
    """How to handle context that exceeds the model's window."""

    DROP_OLDEST = "drop_oldest"  # drop earliest messages (ring buffer)
    SUMMARIZE = "summarize"  # compress oldest messages via summarizer
    TRUNCATE_MIDDLE = "truncate_middle"  # drop middle messages, keep edges
    FAIL = "fail"  # raise if context exceeds window


@dataclass
class PreparedContext:
    """Output of ``prepare_context`` — ready to send to the model."""

    messages: list[dict]
    model: str
    total_tokens: int = 0
    max_tokens: int = 0
    truncated: bool = False
    truncation_strategy: str = ""
    summary_used: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "message_count": len(self.messages),
            "model": self.model,
            "total_tokens": self.total_tokens,
            "max_tokens": self.max_tokens,
            "truncated": self.truncated,
            "truncation_strategy": self.truncation_strategy,
            "summary_used": self.summary_used,
            "metadata": self.metadata,
        }


@dataclass
class ContextSummary:
    """Output of ``summarize`` — a compressed version of the context."""

    summary: str
    original_message_count: int = 0
    original_token_count: int = 0
    summary_token_count: int = 0
    compression_ratio: float = 0.0
    model: str = ""

    def to_dict(self) -> dict:
        return {
            "summary": self.summary[:200],
            "original_message_count": self.original_message_count,
            "original_token_count": self.original_token_count,
            "summary_token_count": self.summary_token_count,
            "compression_ratio": round(self.compression_ratio, 2),
            "model": self.model,
        }


# Token estimator: (messages) -> int
TokenEstimator = Callable[[list[dict]], int]


# ── Context Manager ────────────────────────────────────────────────────────


class ContextManager:
    """Prepares and summarises context for inference requests.

    This manager **never switches models** — if the context is too large
    for the model, it truncates or summarises in-place.

    Usage::

        cm = ContextManager()
        prepared = cm.prepare_context(
            messages=[...],
            model="gpt-4o",
            max_tokens=8192,
        )
        if prepared.truncated:
            logger.warning("Context was truncated")
    """

    def __init__(
        self,
        default_strategy: TruncationStrategy = TruncationStrategy.SUMMARIZE,
        summarizer: Callable[[list[dict]], str] | None = None,
        token_estimator: TokenEstimator | None = None,
    ) -> None:
        self._default_strategy = default_strategy
        self._summarizer = summarizer or _default_summarizer
        self._token_estimator = token_estimator or _default_token_estimator
        self._model_windows: dict[str, int] = {}  # model -> max_context_tokens

    def register_model_window(self, model: str, max_tokens: int) -> None:
        """Register the maximum context window for a model.

        This is used by ``prepare_context`` to determine if truncation
        is needed.  If not registered, the *max_tokens* parameter passed
        to ``prepare_context`` is used.
        """
        self._model_windows[model] = max_tokens
        logger.debug("Registered context window for %s: %d tokens", model, max_tokens)

    # ── Prepare ─────────────────────────────────────────────────────────

    def prepare_context(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int | None = None,
        strategy: TruncationStrategy | None = None,
        reserve_output_tokens: int = 2048,
    ) -> PreparedContext:
        """Prepare a message list for inference with *model*.

        Truncates or summarises the context if it exceeds the model's
        window (minus *reserve_output_tokens*).  **Never switches models.**

        Parameters
        ----------
        messages : list[dict]
            The message list (OpenAI format: ``{"role": ..., "content": ...}``).
        model : str
            The model name.  Used to look up the context window.
        max_tokens : int | None
            Override the model's context window.  If ``None``, uses the
            registered window or falls back to 8192.
        strategy : TruncationStrategy | None
            Override the default truncation strategy.  ``None`` = use
            the default set at construction time.
        reserve_output_tokens : int
            Tokens to reserve for the model's response (subtracted from
            the context budget).
        """
        strategy = strategy or self._default_strategy
        window = max_tokens or self._model_windows.get(model, 8192)
        budget = window - reserve_output_tokens
        total_tokens = self._token_estimator(messages)

        if total_tokens <= budget:
            # No truncation needed
            return PreparedContext(
                messages=messages,
                model=model,
                total_tokens=total_tokens,
                max_tokens=window,
                truncated=False,
                truncation_strategy=strategy.value,
                metadata={"budget": budget, "reserve_output_tokens": reserve_output_tokens},
            )

        logger.info(
            "Context too large for %s: %d tokens (budget=%d). "
            "Applying strategy=%s",
            model, total_tokens, budget, strategy.value,
        )

        if strategy == TruncationStrategy.FAIL:
            raise ContextOverflowError(
                f"Context of {total_tokens} tokens exceeds budget of {budget} "
                f"for model {model} and strategy is 'fail'"
            )

        if strategy == TruncationStrategy.DROP_OLDEST:
            messages = self._truncate_drop_oldest(messages, budget)

        elif strategy == TruncationStrategy.TRUNCATE_MIDDLE:
            messages = self._truncate_middle(messages, budget)

        elif strategy == TruncationStrategy.SUMMARIZE:
            messages, summary_used = self._truncate_summarize(messages, budget, model)

        else:
            # Fallback: drop oldest
            messages = self._truncate_drop_oldest(messages, budget)

        new_total = self._token_estimator(messages)
        return PreparedContext(
            messages=messages,
            model=model,
            total_tokens=new_total,
            max_tokens=window,
            truncated=True,
            truncation_strategy=strategy.value,
            summary_used=(strategy == TruncationStrategy.SUMMARIZE),
            metadata={
                "original_tokens": total_tokens,
                "budget": budget,
                "reserve_output_tokens": reserve_output_tokens,
                "dropped_messages": len(messages) - new_total,
            },
        )

    # ── Summarize ───────────────────────────────────────────────────────

    def summarize(
        self,
        messages: list[dict],
        model: str,
        target_tokens: int = 512,
    ) -> ContextSummary:
        """Summarise a message list into a compact string.

        The summarizer function is called with the full message list and
        returns a concise summary string.  This is used internally by
        ``prepare_context`` when the strategy is ``SUMMARIZE``, and can
        also be called directly for standalone summarisation needs (e.g.
        persisting conversation summaries to a database).

        **Never switches models** — the summary is produced by the
        summarizer callback, not by routing to a different model.
        """
        original_count = len(messages)
        original_tokens = self._token_estimator(messages)

        summary_text = self._summarizer(messages)
        summary_tokens = self._token_estimator([{"role": "system", "content": summary_text}])

        return ContextSummary(
            summary=summary_text,
            original_message_count=original_count,
            original_token_count=original_tokens,
            summary_token_count=summary_tokens,
            compression_ratio=(
                summary_tokens / original_tokens if original_tokens > 0 else 1.0
            ),
            model=model,
        )

    # ── Truncation strategies ───────────────────────────────────────────

    def _truncate_drop_oldest(
        self,
        messages: list[dict],
        budget: int,
    ) -> list[dict]:
        """Drop oldest messages (keep system prompt + most recent)."""
        # Always keep the system message (first message if role='system')
        kept: list[dict] = []
        system_msgs: list[dict] = []
        rest: list[dict] = []

        for m in messages:
            if m.get("role") == "system":
                system_msgs.append(m)
            else:
                rest.append(m)

        # Start with system messages, then add most recent messages
        # until we hit the budget
        kept = list(system_msgs)
        for m in reversed(rest):
            candidate = kept + [m]
            if self._token_estimator(candidate) <= budget:
                kept = candidate
            else:
                break

        # Ensure we have at least one non-system message
        if len(kept) <= len(system_msgs) and rest:
            kept.append(rest[-1])

        logger.debug(
            "drop_oldest: %d → %d messages (budget=%d)",
            len(messages), len(kept), budget,
        )
        return kept

    def _truncate_middle(
        self,
        messages: list[dict],
        budget: int,
    ) -> list[dict]:
        """Drop messages from the middle, keeping the beginning and end."""
        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        if not non_system:
            return messages

        # Always keep the most recent message
        kept = list(system_msgs)
        kept.append(non_system[-1])

        # Work backwards adding older messages until budget is exceeded
        for m in reversed(non_system[:-1]):
            candidate = [m] + kept[len(system_msgs):]
            full = system_msgs + candidate
            if self._token_estimator(full) <= budget:
                kept = system_msgs + candidate
            else:
                break

        logger.debug(
            "truncate_middle: %d → %d messages (budget=%d)",
            len(messages), len(kept), budget,
        )
        return kept

    def _truncate_summarize(
        self,
        messages: list[dict],
        budget: int,
        model: str,
    ) -> tuple[list[dict], bool]:
        """Summarize older messages to fit within *budget*.

        Returns ``(messages, summary_used)`` where *summary_used* is
        ``True`` if summarization was actually applied.
        """
        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        if not non_system:
            return messages, False

        # Keep the most recent N messages, summarize the rest
        # Reserve space for the summary + recent messages
        recent_count = min(5, len(non_system))
        recent = non_system[-recent_count:]
        to_summarize = non_system[:-recent_count]

        if not to_summarize:
            return messages, False

        summary_text = self._summarizer(to_summarize)
        summary_msg = {"role": "system", "content": f"[Summary of earlier context]: {summary_text}"}

        # Check if the summary + recent fits
        kept = system_msgs + [summary_msg] + recent
        if self._token_estimator(kept) <= budget:
            logger.debug(
                "summarize: %d → %d messages (summary=%d chars)",
                len(messages), len(kept), len(summary_text),
            )
            return kept, True

        # Still too large — drop oldest from recent
        kept = self._truncate_drop_oldest(kept, budget)
        return kept, True


# ── Exceptions ──────────────────────────────────────────────────────────────


class ContextOverflowError(Exception):
    """Raised when context exceeds the model's window and strategy is 'fail'."""
    pass


# ── Default implementations ────────────────────────────────────────────────


def _default_summarizer(messages: list[dict]) -> str:
    """Default summarizer: concatenates message content into a brief summary.

    In production this would call an LLM; here we produce a simple
    concatenation as a reasonable fallback.
    """
    parts: list[str] = []
    for m in messages:
        role = m.get("role", "unknown")
        content = m.get("content", "")
        if isinstance(content, str):
            parts.append(f"{role}: {content[:200]}")
        elif isinstance(content, list):
            # Handle multimodal content arrays
            texts = [
                c.get("text", "") for c in content if isinstance(c, dict) and "text" in c
            ]
            parts.append(f"{role}: {' '.join(texts)[:200]}")
    if not parts:
        return ""

    summary = " | ".join(parts)
    # Keep the summary under ~2000 chars
    return summary[:2000]


def _default_token_estimator(messages: list[dict]) -> int:
    """Rough token estimator: 4 chars ≈ 1 token.

    This is intentionally simple.  In production, use tiktoken or
    the model's actual tokenizer for accurate counts.
    """
    total = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            total += len(content) // 4
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    total += len(part["text"]) // 4
                else:
                    total += 50  # non-text content (images, etc.)
        total += 8  # message overhead
    return total + 4  # base request overhead