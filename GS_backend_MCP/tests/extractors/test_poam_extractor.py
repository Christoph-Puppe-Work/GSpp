import pytest
from GS_backend_MCP.myserver.extractors import poam_extractor

def test_get_poam_items():
    poam_data = {
        "plan-of-action-and-milestones": {
            "poam-items": [{"id": "item1", "title": "Fix bug"}]
        }
    }
    items = poam_extractor.get_poam_items(poam_data)
    assert len(items) == 1
    assert items[0]["id"] == "item1"
