from typing import List, Dict, Any
from GSpp_MCP.server.catalog import Catalog
from GSpp_MCP.server.search import SearchIndex

def search_controls(catalog: Catalog, search_index: SearchIndex, query: str) -> List[Dict[str, Any]]:
    """Search for controls using a keyword query."""
    control_ids = search_index.search(query)
    results = []
    for cid in control_ids:
        control = catalog.get_control(cid)
        if control:
            results.append(control)
    return results
