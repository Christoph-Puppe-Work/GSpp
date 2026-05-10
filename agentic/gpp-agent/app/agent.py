"""ADK 2.0 application bootstrap for the gpp-agent."""

import os

import google.auth
from google.adk.apps import App, ResumabilityConfig

from app.agents.orchestrator import get_workflow

# Initialise GCP environment for Vertex AI when ADC is available.
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
except Exception:
    # Local dev without ADC — fine.
    pass


# The Workflow graph is the root agent. ResumabilityConfig persists each
# completed node so HITL pauses (RequestInput) can be resumed safely after
# disconnects, restarts, or long human turn-around times. See
# https://adk.dev/runtime/resume/ .
root_agent = get_workflow()

# `name="gpp_agent_v2"` — separate storage namespace from any leftover
# ADK 1.x sessions that may have used `name="gpp_agent"` or `name="app"`.
app = App(
    name="gpp_agent_v2",
    root_agent=root_agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
)
