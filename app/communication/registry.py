"""Communication provider registry — maps provider names to instances.

ACTIVATION-R1: Uses EmailProvider for real SMTP delivery.
Add WhatsApp or other providers here when available.
"""

from app.communication.providers.email_provider import EmailProvider

providers = {
    "email": EmailProvider(),
}


def get_provider(name="email"):
    """Get a communication provider by name.

    Args:
        name: Provider key (default: "email").

    Returns:
        A CommunicationProvider instance.
    """
    return providers[name]