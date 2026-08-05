import pytest
import os
import json
from unittest.mock import MagicMock, patch
from GS_backend_MCP.myserver import resolver
from GS_backend_MCP.myserver.gcp.storage import OscalModel

@patch("GS_backend_MCP.myserver.gcp.storage.read_oscal_model")
def test_resolve_profile_local_bsi(mock_read_oscal):
    iv_id = "test-iv"
    profile_id = "test-profile"

    # Mock Profile that imports BSI catalog
    bsi_href = "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/refs/heads/main/Anwenderkataloge/Grundschutz%2B%2B/Grundschutz%2B%2B-catalog.json"
    profile_data = {
        "profile": {
            "imports": [{"href": bsi_href}],
            "metadata": {"last-modified": "2023-01-01T00:00:00Z"}
        }
    }

    # Mock storage.read_oscal_model to return our profile_data
    mock_read_oscal.side_effect = lambda iv, model: profile_data if model == OscalModel.PROFILE else None

    # We need to make sure the local catalog file exists for the test
    local_assets_dir = os.path.join(os.path.dirname(resolver.__file__), "..", "assets")
    os.makedirs(local_assets_dir, exist_ok=True)
    local_catalog_path = os.path.join(local_assets_dir, "Grundschutz++-catalog.json")

    dummy_catalog = {"catalog": {"metadata": {"title": "Local BSI Catalog"}, "groups": []}}
    with open(local_catalog_path, "w") as f:
        json.dump(dummy_catalog, f)

    try:
        # Clear cache to ensure we run resolution
        resolver.RESOLVED_CATALOG_CACHE = {}

        resolved = resolver.resolve_profile(iv_id, profile_id)

        assert resolved["catalog"]["metadata"]["title"] == "Local BSI Catalog"
        # Verify storage.read_oscal_model(iv_id, OscalModel.CATALOG) was NOT called
        # It was called once for PROFILE
        assert mock_read_oscal.call_count == 1
    finally:
        # Cleanup
        if os.path.exists(local_catalog_path):
             pass # keep it for real use if needed, but here it's in a temp-like way if we were in a temp dir
