"""Backward-compatibility shim — see ``gpp_agent.agent`` for the real entrypoint.

The previous version of this module attempted to construct an ``App`` with a
``session_service=`` keyword argument, which is not a valid field on
``google.adk.apps.app.App`` (Pydantic ``extra="forbid"``). It also lived in a
location that ADK's auto-discovery did not look at, so it was never actually
exercised. The agent now lives in ``gpp_agent/agent.py`` (the location ADK's
``AgentLoader`` searches for ``app`` and ``root_agent``).

This file is kept only to avoid breaking external callers that still do
``from gpp_agent.app import app``.
"""

from __future__ import annotations

from .agent import app, root_agent

# Legacy aliases
gpp_agent = app

__all__ = ["app", "root_agent", "gpp_agent"]
