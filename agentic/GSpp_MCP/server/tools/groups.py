from typing import Any, Dict, List, Optional
from GSpp_MCP.server.catalog import Catalog

def get_group(catalog: Catalog, group_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific group by ID."""
    return catalog.get_group(group_id)

def list_groups(catalog: Catalog) -> List[Dict[str, Any]]:
    """List all groups in the catalog."""
    return catalog.list_groups()
