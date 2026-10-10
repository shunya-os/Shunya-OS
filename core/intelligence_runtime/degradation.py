"""Graceful Degradation Handler — ensures the runtime never crashes on failure.

When an engine or provider fails, the handler:
  (a) logs the failure with full context
  (b) attempts a fallback path
  (c) returns a truthful degraded-response rather than crashing

G3 Phase 7.4.
"""

from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

logger = logging.getLogger(__name__)


class GracefulDegradationHandler:
    """Wraps engine calls with structured fallback and truthful degradation."""

    @staticmethod
    def execute(
        component_name: str,
        fn: Callable[..., Any],
        fallback_fn: Callable[..., Any] | None = None,
        context: dict[str, Any] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> tuple[Any, dict[str, Any]]:
        """Execute *fn*, falling back if it fails.

        Args:
            component_name: Human-readable name for logging (e.g. "memory.store")
            fn: Primary function to attempt.
            fallback_fn: Optional fallback if primary fails.
            context: Optional structured context for the log.
            *args, **kwargs: Passed to *fn* (and *fallback_fn* on fallback).

        Returns:
            (result, degradation_info) where degradation_info is a dict:
              {"degraded": False, ...} on success
              {"degraded": True, "reason": ..., "fallback_used": ...} on failure
        """
        try:
            result = fn(*args, **kwargs)
            return result, {"degraded": False}
        except Exception as exc:
            detail = {
                "component": component_name,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "context": context or {},
            }
            logger.warning(
                "DEGRADATION [%s]: %s\n%s",
                component_name,
                exc,
                traceback.format_exc(),
            )

            # Attempt fallback
            if fallback_fn is not None:
                try:
                    result = fallback_fn(*args, **kwargs)
                    logger.info(
                        "DEGRADATION [%s]: fallback succeeded",
                        component_name,
                    )
                    return result, {
                        "degraded": True,
                        "reason": str(exc),
                        "fallback_used": True,
                    }
                except Exception as fb_exc:
                    logger.warning(
                        "DEGRADATION [%s]: fallback also failed: %s",
                        component_name,
                        fb_exc,
                    )
                    return None, {
                        "degraded": True,
                        "reason": str(exc),
                        "fallback_used": True,
                        "fallback_error": str(fb_exc),
                    }

            # No fallback — return degraded signal
            return None, {
                "degraded": True,
                "reason": str(exc),
                "fallback_used": False,
            }

    @staticmethod
    def degraded_response(
        original_error: str,
        fallback_hint: str = "",
        component: str = "",
    ) -> dict[str, Any]:
        """Build a truthful degraded response payload.

        The caller MUST NOT fabricate or guess an answer — the response
        truthfully reports the failure instead.
        """
        msg = f"I encountered an issue in {component}: {original_error}"
        if fallback_hint:
            msg += f" {fallback_hint}"
        return {
            "content": msg,
            "status": "degraded",
            "degraded": True,
            "component": component,
            "error": original_error,
        }