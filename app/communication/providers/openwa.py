from app.communication.base import CommunicationProvider


class OpenWAProvider(CommunicationProvider):
    def _do_send(self, to, message, metadata):
        print(f"[OPENWA MOCK] Sending to {to}: {message}")
        return {
            "status": "sent",
            "provider": "openwa",
            "to": to,
            "message": message
        }