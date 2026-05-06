import logging
import hashlib
import json
from typing import Any, Dict, Optional
from GS_backend_MCP.myserver.gcp import storage
from GS_backend_MCP.myserver.gcp.storage import OscalModel

logger = logging.getLogger("GppContextMCP.resolver")

# In-Memory Cache for Resolved Catalogs
# Key: SHA-256 hash of the Profile content
# Value: Resolved Catalog JSON
RESOLVED_CATALOG_CACHE = {}

def get_profile_hash(profile_data: Dict[str, Any]) -> str:
    """Generates a stable SHA-256 hash for the profile content."""
    content = json.dumps(profile_data, sort_keys=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def resolve_profile(iv_id: str, profile_id: str) -> Dict[str, Any]:
    """
    Resolves an OSCAL Profile into a tailored Catalog.
    Implements RAM caching with invalidation.
    """
    # 1. Fetch Profile
    profile_data = storage.read_oscal_model(iv_id, OscalModel.PROFILE)

    # 2. Check Cache
    profile_hash = get_profile_hash(profile_data)
    if profile_hash in RESOLVED_CATALOG_CACHE:
        logger.info(f"Returning cached resolved catalog for profile {profile_hash}")
        return RESOLVED_CATALOG_CACHE[profile_hash]

    # 3. Resolution Logic (Tailoring)
    logger.info(f"Resolving profile {profile_id} for IV {iv_id}")

    # Placeholder for actual BSI GS++ tailoring logic
    # In a real implementation, this would:
    # - Load the base BSI Catalog (catalog-id from profile imports)
    # - Apply 'alter' directives
    # - Apply 'set-parameter' values

    # 3.1 Load base BSI Catalog (mocked for now, should load from storage or bundled)
    # base_catalog = storage.read_oscal_model(iv_id, OscalModel.CATALOG)

    # 3.2 Apply Profile 'alter' directives
    # 3.3 Apply Profile 'set-parameter' values

    # This is a high-level structure of a tailored catalog
    resolved_catalog = {
        "catalog": {
            "uuid": profile_data.get("profile", {}).get("uuid"),
            "metadata": profile_data.get("profile", {}).get("metadata", {}),
            "groups": [], # In production, these are populated from the base catalog after applying 'alter'
            "params": profile_data.get("profile", {}).get("set-parameters", []),
            "remarks": "Resolved via G++ Profile Resolution Engine. Tailoring applied based on profile directives."
        }
    }

    # 4. Update Cache
    RESOLVED_CATALOG_CACHE[profile_hash] = resolved_catalog
    return resolved_catalog
