# agentic/_adk_apps/gpp_agent/agent.py
"""Re-export für ADK CLI auto-discovery (`adk web _adk_apps`)."""
import asyncio
import sys
from pathlib import Path

# Echtes gpp_agent-Modul auf den Import-Pfad legen
GPP_AGENT_ROOT = Path(__file__).resolve().parents[2] / "gpp_agent"
sys.path.insert(0, str(GPP_AGENT_ROOT))

from agents.orchestrator import get_orchestrator

root_agent = get_orchestrator()
root_agent.name = "gpp_agent"