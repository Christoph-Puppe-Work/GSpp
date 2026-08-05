from typing import Any, Dict, List

def get_poam_items(poam_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extracts POA&M items from Plan of Action and Milestones."""
    poam = poam_data.get("plan-of-action-and-milestones", {})
    return poam.get("poam-items", [])
