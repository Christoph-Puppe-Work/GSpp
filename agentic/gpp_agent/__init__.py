"""gpp_agent — multi-agent ADK system for BSI Grundschutz++ workflows.

Importing this package is intentionally cheap: it does NOT eagerly construct
the agent tree. The real entrypoint is ``gpp_agent.agent`` (which exposes the
ADK ``app`` and ``root_agent`` discovery hooks). See ``gpp_agent/agent.py``
for details.
"""
