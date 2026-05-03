import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class Catalog:
    def __init__(self, catalog_path: str, mapping_path: str):
        self.catalog_path = catalog_path
        self.mapping_path = mapping_path
        self.controls: Dict[str, Dict[str, Any]] = {}
        self.groups: Dict[str, Dict[str, Any]] = {}
        self.zielobjekt_map: Dict[str, List[str]] = {}

        self._load_data()
        self._index_catalog()

    def _load_data(self):
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                self.raw_catalog = json.load(f)
            with open(self.mapping_path, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
                # Assuming the structure from zielobjekt_controls.json
                self.zielobjekt_map = mapping_data.get("zielobjekt_controls_map", {})
        except Exception as e:
            logger.error(f"Failed to load catalog or mapping data: {e}")
            raise

    def _index_catalog(self):
        catalog = self.raw_catalog.get("catalog", {})
        groups = catalog.get("groups", [])
        self._traverse_groups(groups)

    def _traverse_groups(self, groups: List[Dict[str, Any]], parent_id: Optional[str] = None):
        for group in groups:
            group_id = group.get("id")
            if not group_id:
                continue

            # Index group metadata
            self.groups[group_id] = {
                "id": group_id,
                "title": self._ensure_string_title(group.get("title")),
                "class": group.get("class"),
                "parent_id": parent_id
            }

            # Index controls in this group
            if "controls" in group:
                self._traverse_controls(group["controls"], group_id)

            # Recurse into subgroups
            if "groups" in group:
                self._traverse_groups(group["groups"], group_id)

    def _traverse_controls(self, controls: List[Dict[str, Any]], group_id: str):
        for control in controls:
            control_id = control.get("id")
            if not control_id:
                continue

            # Extract prose and guidance from parts
            prose = ""
            guidance = ""
            for part in control.get("parts", []):
                if part.get("name") == "prose" or part.get("name") == "statement":
                    prose = part.get("prose", "").strip()
                elif part.get("name") == "guidance":
                    guidance = part.get("prose", "").strip()

            # Extract props
            props = {prop.get("name"): prop.get("value") for prop in control.get("props", []) if prop.get("name")}

            self.controls[control_id] = {
                "id": control_id,
                "title": self._ensure_string_title(control.get("title")),
                "group_id": group_id,
                "prose": prose,
                "guidance": guidance,
                "props": props,
                # Store full control for expanded retrieval if needed
                "raw": control
            }

            # Recurse into sub-controls if any
            if "controls" in control:
                self._traverse_controls(control["controls"], group_id)

    def _ensure_string_title(self, title_value: Any) -> str:
        if isinstance(title_value, list) and title_value:
            return str(title_value[0])
        elif isinstance(title_value, str):
            return title_value
        return ""

    def get_control(self, control_id: str) -> Optional[Dict[str, Any]]:
        return self.controls.get(control_id)

    def list_controls(self) -> List[Dict[str, Any]]:
        return list(self.controls.values())

    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        return self.groups.get(group_id)

    def list_groups(self) -> List[Dict[str, Any]]:
        return list(self.groups.values())

    def list_zielobjektkategorien(self) -> List[str]:
        return list(self.zielobjekt_map.keys())

    def controls_for_zielobjekt(self, category_id: str) -> List[str]:
        return self.zielobjekt_map.get(category_id, [])
