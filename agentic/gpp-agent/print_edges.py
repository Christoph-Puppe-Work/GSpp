import os
os.environ["ANWENDER_MCP_URL"] = "dummy"
os.environ["BACKEND_MCP_URL"] = "dummy"
from app.agent import root_agent
for e in root_agent.graph.edges:
    print(f"From: {e.from_node.name}, To: {e.to_node.name}, Route: {e.route}")
