import logging
import os
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List, Optional
from GSpp_MCP.server.catalog import Catalog
from GSpp_MCP.server.search import SearchIndex
from GSpp_MCP.server.tools import controls, groups, zielobjekte, search, validation

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GSpp-MCP")

CATALOG_PATH = os.getenv("CATALOG_PATH", "GSpp_MCP/data/Grundschutz++-catalog.json")
MAPPING_PATH = os.getenv("MAPPING_PATH", "GSpp_MCP/data/zielobjekt_controls.json")

logger.info(f"Loading catalog from {CATALOG_PATH}...")
catalog = Catalog(CATALOG_PATH, MAPPING_PATH)
search_index = SearchIndex()

logger.info("Indexing controls for search...")
for control in catalog.list_controls():
    text = f"{control['id']} {control['title']} {control['prose']} {control['guidance']}"
    search_index.add_document(control["id"], text)

port = int(os.getenv("PORT", "8080"))
mcp = FastMCP(
    "GSpp-MCP",
    host="0.0.0.0",
    port=port,
    # streamable_http_path defaults to "/mcp" — matches test script and Cloud Run
    # stateless_http=True,   # uncomment if you want stateless mode
)
@mcp.tool()
def get_control(control_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific control by ID."""
    return controls.get_control(catalog, control_id)

@mcp.tool()
def get_control_raw(control_id: str) -> Optional[Dict[str, Any]]:
    """Get the raw OSCAL control data by ID. Use only when full OSCAL details are required."""
    return controls.get_control_raw(catalog, control_id)

@mcp.tool()
def list_controls() -> List[Dict[str, Any]]:
    """List all controls in the catalog."""
    return controls.list_controls(catalog)

@mcp.tool()
def get_group(group_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific group by ID."""
    return groups.get_group(catalog, group_id)

@mcp.tool()
def list_groups() -> List[Dict[str, Any]]:
    """List all groups in the catalog."""
    return groups.list_groups(catalog)

@mcp.tool()
def list_zielobjektkategorien() -> List[str]:
    """List all Zielobjektkategorien defined in the catalog mapping."""
    return zielobjekte.list_zielobjektkategorien(catalog)

@mcp.tool()
def controls_for_zielobjekt(category_id: str) -> List[str]:
    """Get control IDs applicable to a specific Zielobjekt category."""
    return zielobjekte.controls_for_zielobjekt(catalog, category_id)

@mcp.tool()
def get_oscal_profile(category_id: str) -> Optional[Dict[str, Any]]:
    """Generate an OSCAL profile for a specific Zielobjekt category."""
    return zielobjekte.get_oscal_profile(catalog, category_id)

@mcp.tool()
def search_controls(query: str) -> List[Dict[str, Any]]:
    """Search for controls using a keyword query."""
    return search.search_controls(catalog, search_index, query)

@mcp.tool()
def verify_oscal_json(json_content: str) -> Dict[str, Any]:
    """Verifies OSCAL JSON content against the BSI OSCAL schemas. Returns status and errors."""
    return validation.verify_oscal_json(json_content)

if __name__ == "__main__":
    # Explicitly read PORT from environment, defaulting to 8080
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting GSpp-MCP server on port {port}")

    mcp.run(transport="streamable-http")