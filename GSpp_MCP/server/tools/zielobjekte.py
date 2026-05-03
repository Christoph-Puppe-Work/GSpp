from typing import List
from GSpp_MCP.server.catalog import Catalog

def list_zielobjektkategorien(catalog: Catalog) -> List[str]:
    """List all Zielobjektkategorien defined in the catalog mapping."""
    return catalog.list_zielobjektkategorien()

def controls_for_zielobjekt(catalog: Catalog, category_id: str) -> List[str]:
    """Get control IDs applicable to a specific Zielobjekt category."""
    return catalog.controls_for_zielobjekt(category_id)
