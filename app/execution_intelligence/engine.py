"""Compatibility stub — execution_intelligence engine archived during Phase 1 consolidation.

Original files: _archive/execution_variants/execution_intelligence/engine.py
This stub provides minimal engine classes for test compatibility.
"""
from app.intelligence.learning import record_outcome, adjust_confidence


class ExecutionHealthEngine:
    def assess(self, *a, **kw):
        return {"status": "healthy", "score": 1.0}


class TimelineIntelligenceEngine:
    def snapshot(self, *a, **kw):
        return {"events": [], "trend": "stable"}


class DependencyGraphEngine:
    def build(self, *a, **kw):
        return {"nodes": [], "edges": []}


class RiskDetectionEngine:
    def assess(self, *a, **kw):
        return {"level": "low", "score": 0.0}


class NextActionEngine:
    def suggest(self, *a, **kw):
        return []


class PortfolioIntelligence:
    def summarize(self, *a, **kw):
        return {"total": 0, "healthy": 0}


class ExplainabilityLayer:
    def explain(self, *a, **kw):
        return {"summary": "", "details": ""}


class RuntimeService:
    def __init__(self, *a, **kw):
        pass