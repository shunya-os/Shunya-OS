"""Universal Asset Intelligence — UCP-07.

Composes exclusively from frozen SHUNYA runtimes.
No Inventory Runtime. No Asset Management Runtime. No CMDB Runtime.
"""

from core.asset_intelligence.engine import AssetIntelligenceEngine
from core.asset_intelligence.models import (
    Asset, AssetEvent, AssetLocation, AssetProfile, AssetRecommendation,
    AssetStatus, AssetType, AssetCategory, HealthStatus, MaintenanceRecord, RiskLevel,
)
from core.asset_intelligence.runtime import AssetIntelligenceRuntime

__all__ = [
    "AssetIntelligenceRuntime", "AssetIntelligenceEngine",
    "Asset", "AssetProfile", "AssetRecommendation", "AssetEvent",
    "AssetLocation", "MaintenanceRecord",
    "AssetStatus", "AssetType", "AssetCategory", "HealthStatus", "RiskLevel",
]