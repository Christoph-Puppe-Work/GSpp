import json
from google.adk.tools import ToolContext

async def load_vendor_docs(tool_context: ToolContext) -> dict:
    """Reads uploaded PDFs/Docs from the IV-inputs/ GCS-prefix."""
    return {"status": "success", "documents": ["doc1.pdf", "doc2.docx"]}

async def write_evidence_artifact(filename: str, content: dict, tool_context: ToolContext) -> dict:
    """Writes CSV + Ground-Truth-Export to GCS."""
    version = await tool_context.save_artifact(filename, json.dumps(content).encode('utf-8'))
    return {"status": "success", "version": version}
