"""Single source of truth for the gpp_agent ADK application.

ADK's agent loader (``google.adk.cli.utils.agent_loader.AgentLoader``) imports
this module as ``gpp_agent.agent`` and picks up the ``app`` symbol below — an
``App`` instance — *in preference to* a bare ``root_agent``. This means the
custom application config defined here is honoured by both:

* ``adk web .``        — Dev UI (scans the workspace root for ``<dir>/agent.py``)
* ``adk api_server .`` — Production FastAPI server. Internally calls
  ``google.adk.cli.fast_api.get_fast_api_app(...)`` and runs **uvicorn** on the
  resulting FastAPI app, so this *is* the "uvicorn for prod" entrypoint.

Why this file exists
--------------------
The previous setup placed a thin shim under ``_adk_apps/gpp_agent/agent.py``
that did ``sys.path.insert(...)`` and re-exported only ``root_agent``. That
shim silently bypassed the ``App`` config entirely, and the ``App(...)`` call
in the old ``app.py`` was itself broken (it passed an unknown
``session_service=`` kwarg to a Pydantic model with ``extra="forbid"``).
Consolidating everything here removes the placeholder directory, makes
discovery follow the standard ADK convention, and ensures the App config is
actually applied.

Firestore session service (TODO)
--------------------------------
``App`` does *not* accept a ``session_service`` field (cf.
``google/adk/apps/app.py``). To plug ``FirestoreSessionService`` back in,
register a URI scheme via a ``services.py`` next to this file (see
``google/adk/cli/service_registry.py``) and pass
``--session_service_uri firestore://<project>/<database>`` to ``adk api_server``.
"""

from __future__ import annotations

import logging
import os

from google.adk.apps.app import App

from .agents.orchestrator import get_orchestrator

logger = logging.getLogger("gpp_agent")


def _maybe_init_error_reporting() -> None:
    """Best-effort Cloud Error Reporting init; no-op locally / on import errors."""
    try:
        from google.cloud import error_reporting  # imported lazily

        error_reporting.Client()
        logger.info("Google Cloud Error Reporting initialised.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not initialise Error Reporting: %s", exc)


def _build_app() -> App:
    _maybe_init_error_reporting()

    orchestrator = get_orchestrator()
    if hasattr(orchestrator, "name"):
        orchestrator.name = "gpp_agent"

    return App(
        name="gpp_agent",
        root_agent=orchestrator,
        plugins=[],
    )


# ---------------------------------------------------------------------------
# ADK auto-discovery hooks. Order matters for readability only — the loader
# inspects ``app`` first and falls back to ``root_agent`` if the module exposes
# one without an ``App`` instance.
# ---------------------------------------------------------------------------
app: App = _build_app()
root_agent = app.root_agent

__all__ = ["app", "root_agent"]
