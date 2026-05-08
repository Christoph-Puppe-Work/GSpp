import asyncio
import os
import logging
from google.adk.apps.app import App
from google.adk.integrations.firestore.firestore_session_service import FirestoreSessionService
from google.cloud import firestore
from google.cloud import error_reporting
from agents.orchestrator import get_orchestrator

# Configure logging to DEBUG for better diagnostics
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("gpp_agent")

def create_app() -> App:
    # Initialize Google Cloud Error Reporting
    try:
        error_reporting.Client()
        logger.info("Google Cloud Error Reporting initialized.")
    except Exception as e:
        logger.warning(f"Could not initialize Error Reporting: {e}")

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
        plugins=[]
    )

# Naming the variable 'gpp_agent' helps the ADK loader register the app under this specific name
gpp_agent = create_app()

# Provide 'app' as an alias for uvicorn or CLI auto-discovery compatibility
app = gpp_agent
