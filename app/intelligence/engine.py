from app.intelligence.service import IntelligenceService

class IntelligenceEngine:

    @staticmethod
    def suggest(obj):
        pattern = IntelligenceService.find_pattern(obj)

        if pattern:
            return {
                "decision": pattern.suggested_decision,
                "confidence": pattern.confidence,
                "source": "learned"
            }

        return {
            "decision": None,
            "confidence": 0.0,
            "source": "none"
        }