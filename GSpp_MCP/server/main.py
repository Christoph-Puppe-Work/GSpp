import logging
import os
from mcp.server.fastmcp import FastMCP
from GSpp_MCP.server.catalog import Catalog
from GSpp_MCP.server.search import SearchIndex
from GSpp_MCP.server.tools import controls, groups, zielobjekte, search

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

mcp = FastMCP("GSpp-MCP", host="0.0.0.0", port="8080")

@mcp.tool()
def get_control(control_id: str):
    """Get a specific control by ID."""
    return controls.get_control(catalog, control_id)

@mcp.tool()
def list_controls():
    """List all controls in the catalog."""
    return controls.list_controls(catalog)

@mcp.tool()
def get_group(group_id: str):
    """Get a specific group by ID."""
    return groups.get_group(catalog, group_id)

@mcp.tool()
def list_groups():
    """List all groups in the catalog."""
    return groups.list_groups(catalog)

@mcp.tool()
def list_zielobjektkategorien():
    """List all Zielobjektkategorien defined in the catalog mapping."""
    return zielobjekte.list_zielobjektkategorien(catalog)

@mcp.tool()
def controls_for_zielobjekt(category_id: str):
    """Get control IDs applicable to a specific Zielobjekt category."""
    return zielobjekte.controls_for_zielobjekt(catalog, category_id)

@mcp.tool()
def search_controls(query: str):
    """Search for controls using a keyword query."""
    return search.search_controls(catalog, search_index, query)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")