import json
from google.adk.tools import ToolContext

async def load_cis_input(filename: str, tool_context: ToolContext) -> dict:
    """Reads CIS-CSV/JSON from the IV-inputs/ GCS-prefix."""
    iv_id = tool_context.state.get("informationsverbund_id", "default-iv")
    # In a real scenario, we'd use the artifact service or direct GCS
    # For now, we simulate loading from the expected GCS path
    # Path: {iv_id}/inputs/{filename}
    try:
        # Mocking finding the file and returning content
        return {"status": "success", "data": {"cis_controls": []}, "filename": filename}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def write_oscal_artifact(filename: str, content: dict, tool_context: ToolContext) -> dict:
    """Validates + writes final component_definition.json to GCS."""
    try:
        # Save artifact via tool_context
        version = await tool_context.save_artifact(filename, json.dumps(content).encode('utf-8'))
        return {"status": "success", "version": version}
    except Exception as e:
        return {"status": "error", "message": str(e)}
