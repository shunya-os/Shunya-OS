"""SHUNYA Campaign — abstract provider model for campaign management.

Provides the abstract CampaignProvider base class, concrete adapters for
Meta and Google campaigns, and the CampaignRegistry for provider discovery.
"""

from .adapter import (
    CampaignProvider,
    MetaCampaignAdapter,
    GoogleCampaignAdapter,
    CampaignRegistry,
)

__all__ = [
    "CampaignProvider",
    "MetaCampaignAdapter",
    "GoogleCampaignAdapter",
    "CampaignRegistry",
]