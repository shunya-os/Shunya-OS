"""
SHUNYA — Communication Package (Phase 3)
"""
from .models import (CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope,
                     ExternalConversation, ExternalMessage, ExternalParticipant,
                     ExternalAttachmentReference, SyncCursor, OAuthState)
from .adapter import CommunicationAdapter, AdapterCapabilities
from .policy import CaptureEnforcer, CaptureVerdict
from .normalizer import MessageNormalizer
from .oauth import GmailOAuthService, OAuthConfig