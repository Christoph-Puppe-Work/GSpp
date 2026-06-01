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


def validate_enhanced_profile_structure(profile: dict) -> list:
    """Structurally validates a generated enhanced OSCAL profile.

    The repo has no bundled OSCAL profile JSON schema (the only schema path in the code is a
    component schema that is not present), so rather than validate against a full schema we
    check the invariants the pipeline must uphold for the `modify.alters[].adds[]` mechanism
    to resolve and for downstream apps to read the maturity parts (issue 3.3):

    * required top-level fields (profile / uuid / metadata.oscal-version / imports);
    * each alter has a `control-id` and at least one `adds`;
    * each `adds` has a `by-id` and `position` in the OSCAL-allowed set;
    * each added part is a `statement` with an id and prose;
    * all added part ids are unique within the profile.

    Returns a list of human-readable problem strings (empty list == valid).
    """
    problems = []
    prof = (profile or {}).get("profile")
    if not isinstance(prof, dict):
        return ["missing top-level 'profile' object"]

    if not prof.get("uuid"):
        problems.append("profile.uuid is missing")
    meta = prof.get("metadata") or {}
    if not meta.get("oscal-version"):
        problems.append("profile.metadata.oscal-version is missing")
    if not prof.get("imports"):
        problems.append("profile.imports is missing or empty")

    allowed_positions = {"before", "after", "starting", "ending"}
    seen_part_ids = set()

    for ai, alter in enumerate(((prof.get("modify") or {}).get("alters") or [])):
        if not alter.get("control-id"):
            problems.append(f"alters[{ai}] has no control-id")
        adds = alter.get("adds") or []
        if not adds:
            problems.append(f"alters[{ai}] ({alter.get('control-id')}) has no adds")
        for di, add in enumerate(adds):
            if not add.get("by-id"):
                problems.append(f"alters[{ai}].adds[{di}] has no by-id anchor")
            if add.get("position") not in allowed_positions:
                problems.append(
                    f"alters[{ai}].adds[{di}] has invalid position {add.get('position')!r}"
                )
            for pi, part in enumerate(add.get("parts") or []):
                loc = f"alters[{ai}].adds[{di}].parts[{pi}]"
                if part.get("name") != "statement":
                    problems.append(f"{loc} name is {part.get('name')!r}, expected 'statement'")
                pid = part.get("id")
                if not pid:
                    problems.append(f"{loc} has no id")
                elif pid in seen_part_ids:
                    problems.append(f"{loc} duplicate part id {pid!r}")
                else:
                    seen_part_ids.add(pid)
                if not part.get("prose"):
                    problems.append(f"{loc} ({pid}) has empty prose")

    return problems

def _find_statement_part_id(control: dict) -> str:
    """Returns the id of the control's 'statement' part, or None if it has none.

    OSCAL profile `adds` blocks anchor new sub-statements to an existing part via
    `by-id`. The G++ catalog names statement parts `{control_id}_stm`, but rather than
    assume that convention we read the actual id of the part whose name is "statement".
    """
    for part in control.get("parts", []) or []:
        if part.get("name") == "statement" and part.get("id"):
            return part["id"]
    return None


def extract_all_gpp_controls(catalog: dict) -> dict:
    """Recursively extracts all controls from a G++ catalog for quick lookup."""
    controls = {}

    def traverse_controls(control_list):
        for control in control_list:
            control_id = control.get("id")
            if control_id:
                stmt_part_id = _find_statement_part_id(control)
                # Prefer the statement part's prose for the Level 3 baseline; fall
                # back to the first part's prose for controls without a statement part.
                prose = ""
                if control.get("parts"):
                    prose = control["parts"][0].get("prose", "")
                    for part in control["parts"]:
                        if part.get("id") == stmt_part_id:
                            prose = part.get("prose", prose)
                            break
                controls[control_id] = {
                    "title": control.get("title", ""),
                    "prose": prose,
                    "statement_part_id": stmt_part_id,
                }
            # Controls can nest sub-controls (e.g. TEST.2.2.1 under TEST.2.2); these
            # are referenced directly in profiles, so they must be in the lookup too.
            if control.get("controls"):
                traverse_controls(control["controls"])

    def traverse_groups(groups):
        for group in groups:
            traverse_controls(group.get("controls", []))
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
