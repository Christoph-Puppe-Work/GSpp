from typing import Any, Dict, List, Optional
from GSpp_MCP.server.catalog import Catalog

def get_control(catalog: Catalog, control_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific control by ID."""
    return catalog.get_control(control_id)

def list_controls(catalog: Catalog) -> List[Dict[str, Any]]:
    """List all controls in the catalog."""
    return catalog.list_controls()
