import json
import os
from typing import Dict, Any
import jsonschema

def verify_oscal_json(json_content: str) -> Dict[str, Any]:
    """
    Verifies an OSCAL JSON string against the appropriate OSCAL schema.
    Returns a dictionary indicating valid status and any errors.
    """
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON format: {str(e)}"]}
        
    # Determine the OSCAL model from the root key
    model_mapping = {
        "assessment-plan": "oscal_assessment-plan_schema.json",
        "assessment-results": "oscal_assessment-results_schema.json",
        "catalog": "oscal_catalog_schema.json",
        "component-definition": "oscal_component_schema.json",
        "mapping": "oscal_mapping_schema.json",
        "plan-of-action-and-milestones": "oscal_poam_schema.json",
        "profile": "oscal_profile_schema.json",
        "system-security-plan": "oscal_ssp_schema.json"
    }
    
    root_keys = list(data.keys())
    if not root_keys:
        return {"valid": False, "errors": ["Empty JSON object."]}
        
    root_key = root_keys[0]
    if root_key not in model_mapping:
        return {"valid": False, "errors": [f"Root key '{root_key}' is not a recognized OSCAL model. Valid models are: {list(model_mapping.keys())}"]}
        
    schema_filename = model_mapping[root_key]
    # Path logic to find the schema file relative to the project root
    schema_dir = os.getenv("OSCAL_SCHEMAS_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "OSCAL_schemas"))
    schema_path = os.path.normpath(os.path.join(schema_dir, schema_filename))
    
    if not os.path.exists(schema_path):
        return {"valid": False, "errors": [f"Schema file not found at expected path: {schema_path}"]}
        
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except Exception as e:
        return {"valid": False, "errors": [f"Failed to load schema file: {str(e)}"]}
        
    try:
        validator = jsonschema.Draft7Validator(schema)
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        
        if errors:
            error_messages = []
            for error in errors:
                path = ".".join([str(p) for p in error.path]) if error.path else "root"
                error_messages.append(f"Path '{path}': {error.message}")
            return {"valid": False, "errors": error_messages}
            
        return {"valid": True, "errors": []}
    except Exception as e:
        return {"valid": False, "errors": [f"Validation processing error: {str(e)}"]}
