import asyncio
import os
from google.adk.apps.app import App
from google.adk.sessions.firestore import FirestoreSessionService
from google.cloud import firestore
from agents.orchestrator import get_orchestrator

def create_app() -> App:
    # Orchestrator-Agent laden (inklusive aller Sub-Agenten wie ssp_generator)
    orchestrator = asyncio.run(get_orchestrator())
    
    # Firestore Client für Session & State Management
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    db = firestore.Client(project=project_id, database="gpp_agent-db") if project_id else firestore.Client(database="gpp_agent-db")
    
    # Initialisierung des Firestore Session Services (Multi-Tenancy fähig)
    session_service = FirestoreSessionService(
        client=db,
        collection_name="gpp_agent_sessions"
    )
    
    return App(
        # Rename from 'gpp_agent' to 'default' so CopilotKit automatically finds it
        name="default",
        root_agent=orchestrator,
        session_service=session_service,
        plugins=[]
    )

# Die 'app' Instanz wird automatisch von der 'adk web' / 'adk api' CLI gefunden
app = create_app()
