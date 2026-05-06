import asyncio
from GS_backend_MCP.myserver.main import mcp

async def verify_tools():
    # mcp.list_tools() is an async method
    tools_list = await mcp.list_tools()
    tools = [t.name for t in tools_list]
    print(f"Registered tools: {tools}")

    required_tools = [
        "create_oscal_model",
        "update_oscal_model",
        "get_ssp_inventory",
        "get_ssp_implementation",
        "get_assessment_findings",
        "get_assessment_controls",
        "get_assessment_subjects",
        "get_poam_items",
        "list_oscal_models",
        "get_oscal_model_raw",
        "list_oscal_model_versions",
        "get_resolved_profile_catalog"
    ]

    missing = [t for t in required_tools if t not in tools]
    if missing:
        print(f"Missing tools: {missing}")
        exit(1)
    else:
        print("All required tools are registered.")

if __name__ == "__main__":
    asyncio.run(verify_tools())
