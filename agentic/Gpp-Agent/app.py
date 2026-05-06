import asyncio
import os
from google.adk.apps.app import App
from google.adk.plugins import ReflectAndRetryToolPlugin
from google.adk.sessions.firestore import FirestoreSessionService
from google.cloud import firestore
from agents.orchestrator import get_orchestrator

def create_app() -> App:
    # Orchestrator-Agent laden (inklusive aller Sub-Agenten wie ssp_generator)
    orchestrator = asyncio.run(get_orchestrator())
    
    # Firestore Client für Session & State Management
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    db = firestore.Client(project=project_id) if project_id else firestore.Client()
    
    # Initialisierung des Firestore Session Services (Multi-Tenancy fähig)
    session_service = FirestoreSessionService(
        client=db,
        collection_name="gpp_agent_sessions"
    )
    
    return App(
        name="gpp_agent",
        root_agent=orchestrator,
        session_service=session_service,
        plugins=[
            # Integriert das Reflect and Retry Plugin.
            # Wenn der Backend-MCP bei der OSCAL-Validierung einen JSON-Fehler wirft (z.B. fehlendes Feld),
            # fängt das Plugin diesen ab und lässt das LLM das JSON reparieren, ohne den Main-Loop zu stören.
            ReflectAndRetryToolPlugin(max_retries=3)
        ]
    )

# Die 'app' Instanz wird automatisch von der 'adk web' / 'adk api' CLI gefunden
app = create_app()
