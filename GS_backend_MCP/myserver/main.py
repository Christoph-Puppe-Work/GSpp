import logging
import os
import json
from mcp.server.fastmcp import FastMCP
import jsonschema
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from mcp.server.fastmcp import Context
from GS_backend_MCP.myserver.gcp import storage
import jsonpatch
from GS_backend_MCP.myserver.gcp.storage import OscalModel
from GS_backend_MCP.myserver.utils import get_iv_id
from GS_backend_MCP.myserver.extractors import ssp_extractor, assessment_extractor
from GS_backend_MCP.myserver import resolver

# --- Logging & Config -----------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GppContextMCP")
PORT = int(os.getenv("PORT", "8080"))

# --- Schema Pre-Loading (Performance) -------------------------------------
SCHEMA_CACHE = {}

def load_schemas():
    schema_dir = os.path.join(os.path.dirname(__file__), "..", "schemas")
    for model in OscalModel:
        # Map enum to filename
        filename = f"oscal_{model.value}_schema.json"
        path = os.path.join(schema_dir, filename)
        if os.path.exists(path):
            with open(path, 'r') as f:
                SCHEMA_CACHE[model] = json.load(f)
            logger.info(f"Loaded schema for {model.value}")
        else:
            logger.warning(f"Schema file not found: {path}")

logger.info("Pre-loading 8 OSCAL schemas...")
load_schemas()

# --- FastMCP setup --------------------------------------------------------
mcp = FastMCP("GppContextMCP", host="0.0.0.0", port=PORT)

# --- Tool Registration ----------------------------------------------------

@mcp.tool()
def create_oscal_model(model_enum: OscalModel, initial_payload: Dict[str, Any], ctx: Context) -> Dict[str, str]:
    """
    Initializes a new OSCAL model for a tenant.
    Validates against schema and adds required metadata.
    """
    iv_id = get_iv_id(ctx)
    logger.info(f"Creating {model_enum.value} for IV {iv_id}")

    # 1. Draft with Metadata
    draft_doc = initial_payload.copy()

    # Simple metadata injection (OSCAL structures vary, this is a generic placeholder)
    # Usually OSCAL has a top-level object named after the model
    # We should ensure the payload has the expected root key or we wrap it if missing

    # 2. Validation
    schema = SCHEMA_CACHE.get(model_enum)
    if not schema:
        raise RuntimeError(f"Schema for {model_enum.value} not loaded.")

    try:
        jsonschema.validate(instance=draft_doc, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"Validation failed for {model_enum.value}: {e.message}")
        raise RuntimeError(f"Maker-Checker Validation Failed for {model_enum.value}: {e.message} at path {e.json_path}")

    # 3. Commit
    version_name = storage.write_oscal_model(iv_id, model_enum, draft_doc)

    return {
        "status": "success",
        "model": model_enum.value,
        "iv_id": iv_id,
        "version": version_name
    }

@mcp.tool()
def update_oscal_model(model_enum: OscalModel, patch_payload: Dict[str, Any], ctx: Context) -> Dict[str, str]:
    """
    Maker-Checker Loop: Applies patch in RAM, validates locally, commits to GCP.
    patch_payload can be a full document to replace or a JSON merge patch.
    """
    iv_id = get_iv_id(ctx)
    logger.info(f"Updating {model_enum.value} for IV {iv_id}")

    # 1. Read master document (latest snapshot)
    try:
        master_doc = storage.read_oscal_model(iv_id, model_enum)
    except FileNotFoundError:
        raise RuntimeError(f"Cannot update {model_enum.value}: Model does not exist for IV {iv_id}. Use create_oscal_model first.")

    # 2. Patch in RAM (Draft)
    # We support either a full replacement or a JSON patch (if it looks like one)
    # For simplicity, if it's a list, we assume it's a JSON Patch (RFC 6902)
    # If it's a dict, we assume it's a replacement or we could implement a deep merge.

    draft_doc = None
    if isinstance(patch_payload, list):
        try:
            patch = jsonpatch.JsonPatch(patch_payload)
            draft_doc = patch.apply(master_doc)
        except Exception as e:
            raise RuntimeError(f"Failed to apply JSON Patch: {str(e)}")
    else:
        # Shallow merge/replacement for now.
        # In production, this might be a specialized OSCAL merger.
        draft_doc = master_doc.copy()
        draft_doc.update(patch_payload)

    # 3. Local Air-Gapped Validation
    schema = SCHEMA_CACHE.get(model_enum)
    if not schema:
        raise RuntimeError(f"Schema for {model_enum.value} not loaded.")

    try:
        jsonschema.validate(instance=draft_doc, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"Validation failed for {model_enum.value}: {e.message}")
        raise RuntimeError(f"Maker-Checker Validation Failed for {model_enum.value}: {e.message} at path {e.json_path}")

    # 4. Commit to GCP
    version_name = storage.write_oscal_model(iv_id, model_enum, draft_doc)

    return {
        "status": "success",
        "model": model_enum.value,
        "iv_id": iv_id,
        "version": version_name
    }

# --- SSP Tools -----------------------------------------------------------

@mcp.tool()
def get_ssp_inventory(regex_filter: str, ctx: Context) -> List[Dict]:
    """Filters assets from SSP inventory based on a regex."""
    iv_id = get_iv_id(ctx)
    ssp_data = storage.read_oscal_model(iv_id, OscalModel.SSP)
    return ssp_extractor.filter_inventory(ssp_data, regex_filter)

@mcp.tool()
def get_ssp_implementation(status: str, ctx: Context) -> List[Dict]:
    """Extracts controls matching a specific implementation status."""
    iv_id = get_iv_id(ctx)
    ssp_data = storage.read_oscal_model(iv_id, OscalModel.SSP)
    return ssp_extractor.filter_implemented_requirements(ssp_data, status)

# --- Assessment Tools ----------------------------------------------------

@mcp.tool()
def get_assessment_findings(risk_level: str = None, state: str = None, ctx: Context = None) -> List[Dict]:
    """Extracts findings from Assessment Results."""
    iv_id = get_iv_id(ctx)
    ar_data = storage.read_oscal_model(iv_id, OscalModel.ASSESSMENT_RESULTS)
    return assessment_extractor.get_findings(ar_data, risk_level, state)

@mcp.tool()
def get_assessment_controls(regex_filter: str, ctx: Context) -> List[Dict]:
    """Filters controls examined in the assessment."""
    iv_id = get_iv_id(ctx)
    ar_data = storage.read_oscal_model(iv_id, OscalModel.ASSESSMENT_RESULTS)
    return assessment_extractor.filter_assessment_controls(ar_data, regex_filter)

# --- Profile Resolution Tools --------------------------------------------

@mcp.tool()
def get_resolved_profile_catalog(profile_id: str, ctx: Context) -> Dict:
    """Resolves an OSCAL Profile into a tailored Catalog."""
    iv_id = get_iv_id(ctx)
    return resolver.resolve_profile(iv_id, profile_id)

if __name__ == "__main__":
    logger.info(f"Starting GppContextMCP on port {PORT}")
    mcp.run(transport="streamable-http")
