from app.communication.base import CommunicationProvider

class OpenWAProvider(CommunicationProvider):
    def send(self, to, message, metadata=None):
        print(f"[OPENWA MOCK] Sending to {to}: {message}")
        return {
            "status": "sent",
            "provider": "openwa",
            "to": to,
            "message": message
        }