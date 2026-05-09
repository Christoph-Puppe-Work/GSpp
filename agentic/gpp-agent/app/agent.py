import os
import google.auth
from google.adk.apps import App
from google.adk.agents import Agent

from app.agents.orchestrator import get_orchestrator

# Initialize GCP Environment for Vertex AI
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
except Exception:
    pass # Local dev without ADC

# Create the root orchestrator agent
root_agent = get_orchestrator()

# Initialize the ADK App
app = App(
    root_agent=root_agent,
    name="app",
)
