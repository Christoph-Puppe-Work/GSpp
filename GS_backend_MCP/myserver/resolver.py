import logging
import hashlib
import json
import os
from datetime import datetime, timezone
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

    # 3.1 Load base BSI Catalog
    profile = profile_data.get("profile", {})
    imports = profile.get("imports", [])

    base_catalog = None

    # Check if any import points to the official BSI Grundschutz++ catalog URI
    bsi_uri = "BSI-Bund/Stand-der-Technik-Bibliothek/refs/heads/main/Anwenderkataloge/Grundschutz%2B%2B/Grundschutz%2B%2B-catalog.json"
    use_local_bsi = False
    for imp in imports:
        href = imp.get("href", "")
        if bsi_uri in href:
            use_local_bsi = True
            break

    if use_local_bsi:
        local_path = os.path.join(os.path.dirname(__file__), "..", "assets", "Grundschutz++-catalog.json")
        if os.path.exists(local_path):
            logger.info(f"Using local baked-in BSI catalog from {local_path}")
            with open(local_path, "r") as f:
                base_catalog = json.load(f)
        else:
            logger.warning(f"Local BSI catalog not found at {local_path}, falling back to storage.")

    if not base_catalog:
        try:
            base_catalog = storage.read_oscal_model(iv_id, OscalModel.CATALOG)
        except FileNotFoundError:
            logger.warning(f"Base catalog not found for IV {iv_id}. Using empty catalog for resolution.")
            base_catalog = {"catalog": {"groups": [], "metadata": {}}}

    # 3.2 Extract Profile Directives
    profile = profile_data.get("profile", {})
    imports = profile.get("imports", [])
    set_parameters = profile.get("set-parameters", [])

    # 3.3 Apply Profile 'set-parameter' values
    # In OSCAL, parameters can be set in the catalog or profile.
    # Here we merge profile parameters into the catalog's parameter list.
    catalog_obj = base_catalog.get("catalog", {})
    if "params" not in catalog_obj:
        catalog_obj["params"] = []

    # Simple merge of parameters by ID
    param_map = {p["id"]: p for p in catalog_obj["params"]}
    for sp in set_parameters:
        p_id = sp.get("param-id")
        if p_id in param_map:
            param_map[p_id].update(sp)
        else:
            param_map[p_id] = sp

    catalog_obj["params"] = list(param_map.values())

    # 3.4 Apply Profile 'alter' directives (Simplified)
    # In a full implementation, this would handle additions/removals/modifications of controls.
    # For now, we update the metadata to reflect resolution.

    catalog_obj["metadata"]["last-modified"] = datetime.now(timezone.utc).isoformat()
    catalog_obj["remarks"] = f"Resolved via G++ Profile Resolution Engine. Based on profile {profile_id}. Profile Hash: {profile_hash[:8]}"

    resolved_catalog = base_catalog

    # 4. Update Cache
    RESOLVED_CATALOG_CACHE[profile_hash] = resolved_catalog
    return resolved_catalog
