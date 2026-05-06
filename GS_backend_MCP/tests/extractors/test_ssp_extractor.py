import pytest
from GS_backend_MCP.myserver.extractors import ssp_extractor

def test_filter_inventory():
    ssp = {
        "system-security-plan": {
            "system-characteristics": {
                "inventory-items": [
                    {"description": "Web Server", "remarks": "Production"},
                    {"description": "Database", "remarks": "Staging"}
                ]
            }
        }
    }

    # Filter by regex
    results = ssp_extractor.filter_inventory(ssp, "Web")
    assert len(results) == 1
    assert results[0]["description"] == "Web Server"

    # Case insensitive
    results = ssp_extractor.filter_inventory(ssp, "web")
    assert len(results) == 1

    # No match
    results = ssp_extractor.filter_inventory(ssp, "Redis")
    assert len(results) == 0

    # No filter
    results = ssp_extractor.filter_inventory(ssp, "")
    assert len(results) == 2

def test_filter_implemented_requirements():
    ssp = {
        "system-security-plan": {
            "control-implementation": {
                "implemented-requirements": [
                    {"control-id": "AC-1", "status": {"state": "implemented"}},
                    {"control-id": "AC-2", "status": {"state": "planned"}}
                ]
            }
        }
    }

    results = ssp_extractor.filter_implemented_requirements(ssp, "implemented")
    assert len(results) == 1
    assert results[0]["control-id"] == "AC-1"

    results = ssp_extractor.filter_implemented_requirements(ssp, "planned")
    assert len(results) == 1
    assert results[0]["control-id"] == "AC-2"
