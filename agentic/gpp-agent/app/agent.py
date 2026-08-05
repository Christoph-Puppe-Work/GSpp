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

# IMPORTANT: `App.name` MUST equal the agent directory name (here: "app").
# `adk web` and `agents-cli playground` derive the runner's `app_name`
# from the filesystem path (the directory containing `agent.py`). A
# mismatch raises:
#     SessionNotFoundError("...runner is configured with app name 'X', but
#     the root agent was loaded from .../app, which implies app name
#     'app'...").
# Storage isolation from any leftover ADK 1.x sessions is achieved by
# either wiping dev sessions or by renaming the agent directory itself
# (e.g. `app/` → `gpp_agent_v2/`) — NOT via the `App.name` field.
app = App(
    name="app",
    root_agent=root_agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
)
