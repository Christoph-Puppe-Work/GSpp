import json
import logging
import uuid
import os
import csv
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class Catalog:
    def __init__(self, catalog_path: str, mapping_path: str):
        self.catalog_path = catalog_path
        self.mapping_path = mapping_path
        # CSV path is assumed to be in the same directory as the mapping file
        self.csv_path = os.path.join(os.path.dirname(mapping_path), "zielobjektkategorien.csv")

        self.controls: Dict[str, Dict[str, Any]] = {}
        self.groups: Dict[str, Dict[str, Any]] = {}
        self.zielobjekt_map: Dict[str, List[str]] = {}
        self.zielobjekt_name_map: Dict[str, str] = {}

        self._load_data()
        self._index_catalog()

    def _load_data(self):
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                self.raw_catalog = json.load(f)
            with open(self.mapping_path, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
                # Assuming the structure from zielobjekt_controls.json
                if "zielobjekt_controls_map" not in mapping_data:
                    logger.warning(f"Key 'zielobjekt_controls_map' missing in {self.mapping_path}")
                self.zielobjekt_map = mapping_data.get("zielobjekt_controls_map", {})

            if os.path.exists(self.csv_path):
                with open(self.csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'UUID' in row and 'Zielobjekt' in row:
                            self.zielobjekt_name_map[row['UUID'].strip()] = row['Zielobjekt'].strip()
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
                # "raw" removed to reduce memory footprint. Use get_control_raw tool instead.
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

    def get_control_raw(self, control_id: str) -> Optional[Dict[str, Any]]:
        """Finds the raw OSCAL control in the original catalog by its ID."""
        catalog_root = self.raw_catalog.get("catalog", {})
        groups = catalog_root.get("groups", [])
        return self._find_control_raw_recursive(groups, control_id)

    def _find_control_raw_recursive(self, groups: List[Dict[str, Any]], control_id: str) -> Optional[Dict[str, Any]]:
        for group in groups:
            # Check controls in this group
            for control in group.get("controls", []):
                if control.get("id") == control_id:
                    return control
                # Check sub-controls
                found = self._find_sub_control_raw_recursive(control.get("controls", []), control_id)
                if found:
                    return found
            # Check subgroups
            found = self._find_control_raw_recursive(group.get("groups", []), control_id)
            if found:
                return found
        return None

    def _find_sub_control_raw_recursive(self, controls: List[Dict[str, Any]], control_id: str) -> Optional[Dict[str, Any]]:
        for control in controls:
            if control.get("id") == control_id:
                return control
            found = self._find_sub_control_raw_recursive(control.get("controls", []), control_id)
            if found:
                return found
        return None

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

    def get_oscal_profile(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Constructs an OSCAL profile for a given Zielobjekt category."""
        controls = self.controls_for_zielobjekt(category_id)
        if not controls:
            return None

        zielobjekt_name = ""
        if category_id == "Methodik" or category_id.endswith("_prozesse") or category_id.endswith("prozesse"):
            zielobjekt_name = category_id
        elif category_id in self.zielobjekt_name_map:
            zielobjekt_name = self.zielobjekt_name_map[category_id]
        else:
            logger.warning(f"No name found for Zielobjekt with ID {category_id}.")
            zielobjekt_name = category_id

        profile_uuid = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()
        catalog_url = "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/refs/heads/main/Anwenderkataloge/Grundschutz%2B%2B/Grundschutz%2B%2B-catalog.json"

        profile = {
            "profile": {
                "uuid": profile_uuid,
                "metadata": {
                    "title": f"{category_id} {zielobjekt_name}",
                    "last-modified": now_utc,
                    "version": "0.0.1",
                    "oscal-version": "1.1.3"
                },
                "imports": [
                    {
                        "href": catalog_url,
                        "include-controls": [
                            {
                                "with-ids": controls
                            }
                        ]
                    }
                ]
            }
        }
        return profile
