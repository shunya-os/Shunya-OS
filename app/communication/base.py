"""ACTIVATION-07: CommunicationProvider base with hard guardrail.

No message leaves without is_human_triggered=True in metadata.
This is the architectural boundary — AI can propose, only human can send.
"""


class CommunicationProvider:
    def send(self, to, message, metadata=None):
        """Send a message. REQUIRES metadata.is_human_triggered=True.

        Raises:
            PermissionError: If metadata does not contain
                is_human_triggered=True. This is the constitutional
                guardrail: SHUNYA proposes, only human disposes.
        """
        metadata = metadata or {}
        if not metadata.get("is_human_triggered"):
            raise PermissionError(
                "Blocked: non-human send. "
                "SHUNYA constitutional rule: proposals only. "
                "Human must approve before any message is sent."
            )

        return self._do_send(to, message, metadata)

    def _do_send(self, to, message, metadata):
        """Subclasses implement the actual delivery here. Must return result dict."""
        raise NotImplementedError