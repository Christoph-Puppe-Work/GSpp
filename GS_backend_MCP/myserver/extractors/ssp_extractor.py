import re
from typing import Any, Dict, List

def filter_inventory(ssp: Dict[str, Any], regex_filter: str) -> List[Dict[str, Any]]:
    """Filters assets from SSP inventory based on a regex."""
    system_characteristics = ssp.get("system-security-plan", {}).get("system-characteristics", {})
    inventory_items = system_characteristics.get("inventory-items", [])

    if not regex_filter:
        return inventory_items

    pattern = re.compile(regex_filter, re.IGNORECASE)
    filtered = []
    for item in inventory_items:
        # Search in description, remarks, or metadata if available
        search_str = f"{item.get('description', '')} {item.get('remarks', '')}"
        if pattern.search(search_str):
            filtered.append(item)
    return filtered

def filter_implemented_requirements(ssp: Dict[str, Any], status: str) -> List[Dict[str, Any]]:
    """Extracts controls matching a specific implementation status."""
    control_implementation = ssp.get("system-security-plan", {}).get("control-implementation", {})
    implemented_requirements = control_implementation.get("implemented-requirements", [])

    if not status:
        return implemented_requirements

    filtered = []
    for req in implemented_requirements:
        # Check overall status or specific statement status
        # This is a simplified extraction
        if req.get("status", {}).get("state") == status:
            filtered.append(req)
    return filtered
