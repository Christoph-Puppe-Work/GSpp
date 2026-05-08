import asyncio
import os
from google.adk.apps.app import App
from google.adk.sessions.firestore import FirestoreSessionService
from google.cloud import firestore
from agents.orchestrator import get_orchestrator
from google.adk.plugins.copilotkit import CopilotKitPlugin

def create_app() -> App:
    # Orchestrator-Agent laden (inklusive aller Sub-Agenten wie ssp_generator)
    orchestrator = asyncio.run(get_orchestrator())

    # Ensure the root agent name is set to 'gpp_agent' for consistent discovery
    if hasattr(orchestrator, 'name'):
        orchestrator.name = "gpp_agent"
    
    # Firestore Client für Session & State Management
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    db = firestore.Client(project=project_id, database="gpp_agent-db") if project_id else firestore.Client()
    
    # Initialisierung des Firestore Session Services (Multi-Tenancy fähig)
    session_service = FirestoreSessionService(
        client=db,
        collection_name="gpp_agent_sessions"
    )
    
    return App(
        name="gpp_agent",  # This must match the 'appName' in your test script
        root_agent=orchestrator,
        session_service=session_service,
        plugins=[CopilotKitPlugin()]  # Added CopilotKit to resolve the 404 in your logs
    )

# Naming the variable 'gpp_agent' helps the ADK loader register the app under this specific name
gpp_agent = create_app()

# Provide 'app' as an alias for uvicorn or CLI auto-discovery compatibility
app = gpp_agent
