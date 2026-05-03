import json
from google.adk.tools import ToolContext

async def write_policy_artifact(domain: str, content: str, tool_context: ToolContext) -> dict:
    """Writes a domain policy as Markdown/PDF to GCS."""
    filename = f"policy_{domain}.md"
    version = await tool_context.save_artifact(filename, content.encode('utf-8'))
    return {"status": "success", "version": version}
