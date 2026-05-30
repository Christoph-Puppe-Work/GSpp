"""
OSCAL Validation Utilities

This module provides helper functions for working with OSCAL files, primarily
for validating them against their corresponding JSON schemas.
"""

import logging
from jsonschema import validate, ValidationError

from utils.file_utils import read_json_file

logger = logging.getLogger(__name__)

def validate_oscal(json_path: str, schema_path: str) -> bool:
    """
    Validates a JSON file against a given JSON schema.

    Args:
        json_path (str): The path to the JSON file to validate.
        schema_path (str): The path to the JSON schema file.

    Returns:
        bool: True if validation is successful, False otherwise.
    """
    schema = read_json_file(schema_path)
    if not schema:
        logger.error(f"Could not load schema from {schema_path}")
        return False

    # Workaround for https://github.com/python-jsonschema/jsonschema/issues/1213
    # The OSCAL schema uses a Unicode-aware regex that is not supported by the 'regex'
    # format checker in jsonschema. We remove the pattern to allow for structural validation.
    if 'definitions' in schema and 'TokenDatatype' in schema['definitions']:
        if 'pattern' in schema['definitions']['TokenDatatype']:
            del schema['definitions']['TokenDatatype']['pattern']

    instance = read_json_file(json_path)
    if not instance:
        logger.error(f"Could not load JSON instance from {json_path}")
        return False

    try:
        validate(instance=instance, schema=schema)
        logger.info(f"Successfully validated {json_path} against {schema_path}")
        return True
    except ValidationError as e:
        logger.error(f"Validation failed for {json_path}: {e.message}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during validation of {json_path}: {e}")
        return False

def extract_all_gpp_controls(catalog: dict) -> dict:
    """Recursively extracts all controls from a G++ catalog for quick lookup."""
    controls = {}

    def traverse_groups(groups):
        for group in groups:
            for control in group.get("controls", []):
                control_id = control.get("id")
                if control_id:
                    prose = ""
                    guidance = ""
                    for part in control.get("parts", []):
                        if part.get("name") == "statement":
                            prose = part.get("prose", "")
                        elif part.get("name") == "guidance":
                            guidance = part.get("prose", "")

                    # Fallback for old structure if statement name isn't explicit
                    if not prose and control.get("parts"):
                        prose = control.get("parts")[0].get("prose", "")

                    controls[control_id] = {
                        "title": control.get("title", ""),
                        "prose": prose,
                        "guidance": guidance
                    }
            if "groups" in group:
                traverse_groups(group["groups"])

    traverse_groups(catalog.get("catalog", {}).get("groups", []))
    return controls

def get_component_type(baustein_id: str) -> str:
    """Returns the component type based on the Baustein ID format."""
    return "process" if "prozesse" in baustein_id.lower() or "methodik" in baustein_id.lower() else "software"

def normalize_id(id_str: str) -> str:
    """Normalizes an ID string for comparison (lowercase, stripped)."""
    return str(id_str).strip().lower()
