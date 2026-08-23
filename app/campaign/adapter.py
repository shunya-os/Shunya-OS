"""SHUNYA Campaign Adapter — abstract provider pattern for ad campaign management.

Defines the CampaignProvider ABC, concrete adapters for Meta and Google Ads,
and a CampaignRegistry that manages registered campaign providers.
Each adapter handles credential absence gracefully by returning structured
error states rather than raising.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

# ── Error-state constants ──────────────────────────────────────────
ERR_CREDENTIALS_MISSING = "credentials_missing"
ERR_CREDENTIALS_EXPIRED = "credentials_expired"
ERR_API_UNAVAILABLE = "api_unavailable"
ERR_UNKNOWN = "unknown"


class CampaignProvider(ABC):
    """Abstract base for ad campaign providers (Meta, Google, etc.)."""

    name: str = "base"
    required_env_vars: list[str] = []

    def __init__(self):
        self._credential_status: Optional[str] = None

    def check_credentials(self) -> str:
        """Check whether required credentials are available.

        Returns:
            None if credentials are OK, or an error-state constant.
        """
        missing = [v for v in self.required_env_vars if not os.getenv(v)]
        if missing:
            self._credential_status = ERR_CREDENTIALS_MISSING
            logger.warning("%s: missing env vars: %s", self.name, missing)
            return ERR_CREDENTIALS_MISSING

        valid = self._validate_credentials()
        if valid is not None:
            self._credential_status = valid
            return valid

        self._credential_status = None
        return "ok"

    def _validate_credentials(self) -> Optional[str]:
        """Override in subclasses for custom credential validation (e.g. token expiry).

        Return an error-state constant or None if credentials are valid.
        """
        return None

    @abstractmethod
    def create_campaign(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create a campaign.

        Returns a result dict with keys:
            success (bool)
            campaign_id (str)   — provider's campaign ID on success
            data (dict)          — provider-specific campaign data
            error (str)          — error message / state constant on failure
        """
        ...

    @abstractmethod
    def get_status(self, campaign_id: str) -> dict[str, Any]:
        """Get the current status of a campaign.

        Returns a result dict with keys:
            success (bool)
            status (str)         — e.g. "active", "paused", "archived"
            data (dict)          — provider-specific status data
            error (str)
        """
        ...

    @abstractmethod
    def sync(self, config: dict[str, Any]) -> dict[str, Any]:
        """Sync campaign data (pull latest metrics / push updates).

        Returns a result dict with keys:
            success (bool)
            updates (list)       — list of change records
            error (str)
        """
        ...

    def _error_result(self, action: str, reason: str = ERR_CREDENTIALS_MISSING) -> dict[str, Any]:
        """Produce a standard error result when the provider is unavailable."""
        return {
            "success": False,
            "campaign_id": "",
            "data": {},
            "status": "",
            "updates": [],
            "error": reason,
            "provider": self.name,
            "action": action,
            "detail": f"{self.name} cannot {action}: {reason}",
        }


class MetaCampaignAdapter(CampaignProvider):
    """Meta (Facebook/Instagram) Ads campaign provider.

    Requires env vars:
        META_ACCESS_TOKEN
        META_AD_ACCOUNT_ID
    """

    name = "meta"
    required_env_vars = ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"]

    def create_campaign(self, config: dict[str, Any]) -> dict[str, Any]:
        status = self.check_credentials()
        if status != "ok":
            return self._error_result("create_campaign", status)

        try:
            # Placeholder — real integration would call the Facebook Graph API
            # POST /v22.0/act_{ad_account_id}/campaigns
            logger.info("MetaCampaignAdapter.create_campaign called — config keys=%s", list(config.keys()))
            return {
                "success": True,
                "campaign_id": f"meta_camp_{hash(str(config))}",
                "data": {
                    "name": config.get("name", "Untitled Campaign"),
                    "objective": config.get("objective", "OUTCOME_TRAFFIC"),
                    "status": "ACTIVE",
                },
                "error": "",
                "provider": self.name,
                "action": "create_campaign",
            }
        except Exception as exc:
            logger.error("Meta campaign creation failed: %s", exc)
            return self._error_result("create_campaign", ERR_UNKNOWN)

    def get_status(self, campaign_id: str) -> dict[str, Any]:
        status = self.check_credentials()
        if status != "ok":
            return self._error_result("get_status", status)

        try:
            logger.info("MetaCampaignAdapter.get_status called — campaign_id=%s", campaign_id)
            return {
                "success": True,
                "status": "ACTIVE",
                "data": {"campaign_id": campaign_id, "spend": 0.0, "impressions": 0},
                "error": "",
                "provider": self.name,
                "action": "get_status",
            }
        except Exception as exc:
            logger.error("Meta get_status failed: %s", exc)
            return self._error_result("get_status", ERR_UNKNOWN)

    def sync(self, config: dict[str, Any]) -> dict[str, Any]:
        status = self.check_credentials()
        if status != "ok":
            return self._error_result("sync", status)

        try:
            logger.info("MetaCampaignAdapter.sync called")
            return {
                "success": True,
                "updates": [],
                "error": "",
                "provider": self.name,
                "action": "sync",
            }
        except Exception as exc:
            logger.error("Meta sync failed: %s", exc)
            return self._error_result("sync", ERR_UNKNOWN)


class GoogleCampaignAdapter(CampaignProvider):
    """Google Ads campaign provider.

    Requires env vars:
        GOOGLE_ADS_DEVELOPER_TOKEN
        GOOGLE_ADS_CLIENT_ID
        GOOGLE_ADS_CLIENT_SECRET
        GOOGLE_ADS_REFRESH_TOKEN
        GOOGLE_ADS_CUSTOMER_ID
    """

    name = "google"
    required_env_vars = [
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_CUSTOMER_ID",
    ]

    def create_campaign(self, config: dict[str, Any]) -> dict[str, Any]:
        status = self.check_credentials()
        if status != "ok":
            return self._error_result("create_campaign", status)

        try:
            # Placeholder — real integration would call the Google Ads API
            # via google-ads library
            logger.info("GoogleCampaignAdapter.create_campaign called — config keys=%s", list(config.keys()))
            return {
                "success": True,
                "campaign_id": f"google_camp_{hash(str(config))}",
                "data": {
                    "name": config.get("name", "Untitled Campaign"),
                    "type": config.get("campaign_type", "SEARCH"),
                    "status": "ENABLED",
                },
                "error": "",
                "provider": self.name,
                "action": "create_campaign",
            }
        except Exception as exc:
            logger.error("Google campaign creation failed: %s", exc)
            return self._error_result("create_campaign", ERR_UNKNOWN)

    def get_status(self, campaign_id: str) -> dict[str, Any]:
        status = self.check_credentials()
        if status != "ok":
            return self._error_result("get_status", status)

        try:
            logger.info("GoogleCampaignAdapter.get_status called — campaign_id=%s", campaign_id)
            return {
                "success": True,
                "status": "ENABLED",
                "data": {"campaign_id": campaign_id, "cost_micros": 0, "impressions": 0},
                "error": "",
                "provider": self.name,
                "action": "get_status",
            }
        except Exception as exc:
            logger.error("Google get_status failed: %s", exc)
            return self._error_result("get_status", ERR_UNKNOWN)

    def sync(self, config: dict[str, Any]) -> dict[str, Any]:
        status = self.check_credentials()
        if status != "ok":
            return self._error_result("sync", status)

        try:
            logger.info("GoogleCampaignAdapter.sync called")
            return {
                "success": True,
                "updates": [],
                "error": "",
                "provider": self.name,
                "action": "sync",
            }
        except Exception as exc:
            logger.error("Google sync failed: %s", exc)
            return self._error_result("sync", ERR_UNKNOWN)


class CampaignRegistry:
    """Registry for campaign providers.

    Manages the lifecycle of CampaignProvider instances, including
    credential checks and lazy resolution.
    """

    def __init__(self):
        self._providers: dict[str, CampaignProvider] = {}
        self._default_provider: Optional[str] = None

    def register(self, name: str, provider: CampaignProvider, set_default: bool = False) -> None:
        """Register a campaign provider by name."""
        self._providers[name] = provider
        if set_default or self._default_provider is None:
            self._default_provider = name
        logger.info("Campaign provider registered: %s", name)

    def get(self, name: str) -> Optional[CampaignProvider]:
        """Get a registered provider by name."""
        return self._providers.get(name)

    def get_default(self) -> Optional[CampaignProvider]:
        """Get the default campaign provider."""
        if self._default_provider:
            return self._providers.get(self._default_provider)
        return None

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    def resolve(self, preferred: Optional[str] = None) -> Optional[CampaignProvider]:
        """Resolve a campaign provider by preference or default.

        If a preferred provider is named, returns it; otherwise returns
        the default. Consumers should call check_credentials() before use.
        """
        if preferred and preferred in self._providers:
            return self._providers[preferred]
        return self.get_default()

    def available_providers(self) -> list[tuple[str, CampaignProvider]]:
        """Return providers whose credentials are available."""
        results = []
        for name, provider in self._providers.items():
            if provider.check_credentials() == "ok":
                results.append((name, provider))
        return results


# Module-level singleton
_registry = CampaignRegistry()

# Register default campaign providers
_registry.register("meta", MetaCampaignAdapter(), set_default=True)
_registry.register("google", GoogleCampaignAdapter())


def get_registry() -> CampaignRegistry:
    """Get the global campaign provider registry."""
    return _registry