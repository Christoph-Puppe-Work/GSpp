# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Workflow-graph integration tests for the gpp-agent ADK 2.0 Workflow.

These tests exercise the *structure* of the Workflow graph without a live
Gemini call or live MCP servers — they pin the planning.md guarantees:

- 19 nodes (1 START + classifier + classifier_router + 5 phase agents
  + 12 gate function nodes).
- Phase 5 (Remediation) is reachable from Phase 4 (Gatekeeper) **only** via
  the `gate_phase4_decision` node on `route="cleared"`.
- The classifier_router emits the five phase route values plus a chat fallback.
- `gate_phase4_decision` forces `route="blocked"` whenever the underlying
  `phase4_result.cleared_for_audit` is `False`, regardless of the user's
  reply. This is the runtime half of the "P4 is the only gate to P5" rule.

A separate test (`test_live_agent_stream`) exercises the full LLM path with
`InMemoryRunner`; it is opt-in via the `GPP_AGENT_LIVE_TESTS` env var because
it needs Gemini credentials.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

# `app.agent` instantiates MCP toolsets at import time, which need URLs but
# does not actually connect. Provide harmless localhost defaults so the import
# succeeds in CI without real MCP servers.
os.environ.setdefault("ANWENDER_MCP_URL", "http://localhost:9001")
os.environ.setdefault("BACKEND_MCP_URL", "http://localhost:9002")


# ---------------------------------------------------------------------------
# Graph-shape tests (fast, no LLM)
# ---------------------------------------------------------------------------


def test_workflow_has_expected_nodes() -> None:
    """The Workflow graph contains START + classifier + 5 phase agents +
    12 gate function nodes (= 19 nodes total)."""
    from app.agent import root_agent

    node_names = {n.name for n in root_agent.graph.nodes}

    expected = {
        "__START__",
        # Classifier + router
        "classifier",
        "classify_router",
        # Five phase LlmAgents
        "phase1_governance",
        "phase2_mapper",
        "phase3_implementation",
        "phase4_gatekeeper",
        "phase5_remediation",
        # Five HITL gates
        "gate_phase1_request",
        "gate_phase1_ack",
        "gate_phase2_request",
        "gate_phase2_ack",
        "gate_phase3_request",
        "gate_phase3_ack",
        "gate_phase4_request",
        "gate_phase4_decision",
        "gate_phase4_blocked",
        "gate_phase5_request",
        "gate_phase5_ack",
    }
    assert expected.issubset(node_names), (
        f"Missing nodes: {expected - node_names}; extra nodes: {node_names - expected}"
    )
    assert len(node_names) == 19, f"Expected 19 nodes, got {len(node_names)}"


def test_classifier_router_maps_phase_routes_and_chat_fallback() -> None:
    """`classify_router` emits the five canonical route values plus a chat
    fallback that loops back to the classifier."""
    from app.agent import root_agent

    edges_from_router = {
        e.route: e.to_node.name
        for e in root_agent.graph.edges
        if e.from_node.name == "classify_router"
    }
    assert edges_from_router == {
        "chat": "classifier",
        "govern": "phase1_governance",
        "model": "phase2_mapper",
        "track": "phase3_implementation",
        "audit": "phase4_gatekeeper",
        "remediate": "phase5_remediation",
    }


def test_phase4_gate_is_only_path_to_phase5_from_phase4() -> None:
    """Phase 5 has exactly two ingress edges:
        1. from `classify_router`  (route = `remediate`)  — direct request
        2. from `gate_phase4_decision`  (route = `cleared`) — only path from P4

    There is **no** direct edge from `phase4_gatekeeper` to `phase5_remediation`.
    This is the structural half of the "Phase 4 is the only gate to Phase 5"
    invariant.
    """
    from app.agent import root_agent

    p5_in_edges = [
        (e.from_node.name, e.route)
        for e in root_agent.graph.edges
        if e.to_node.name == "phase5_remediation"
    ]
    assert sorted(p5_in_edges) == sorted(
        [
            ("classify_router", "remediate"),
            ("gate_phase4_decision", "cleared"),
        ]
    ), f"Unexpected edges into phase5_remediation: {p5_in_edges}"


def test_phase4_decision_routes_split_cleared_blocked() -> None:
    """`gate_phase4_decision` has exactly two outgoing edges, one for
    `cleared` (→ Phase 5) and one for `blocked` (→ terminal node)."""
    from app.agent import root_agent

    out = {
        e.route: e.to_node.name
        for e in root_agent.graph.edges
        if e.from_node.name == "gate_phase4_decision"
    }
    assert out == {
        "cleared": "phase5_remediation",
        "blocked": "gate_phase4_blocked",
    }


def test_workflow_state_schema_attached() -> None:
    """The Workflow uses our `WorkflowState` Pydantic model as `state_schema`."""
    from app.agent import root_agent
    from app.schemas import WorkflowState

    assert root_agent.state_schema is WorkflowState


# ---------------------------------------------------------------------------
# Phase-4 decision logic — the runtime half of the audit-clearance gate.
# ---------------------------------------------------------------------------


def _ctx_with_state(state: dict) -> SimpleNamespace:
    """Build a minimal mock `InvocationContext` whose `.session.state` reads
    from the provided dict — enough for the gate functions under test."""
    return SimpleNamespace(session=SimpleNamespace(state=state))


def test_route_to_phase_writes_via_tool_context_state() -> None:
    """Tool state writes must go through ToolContext.state so ADK records them
    as state deltas and the next workflow node can read classifier_route.
    The tool must also skip summarization so the classifier does not receive
    its own FunctionResponse and call route_to_phase again."""
    from app.agents.classifier import route_to_phase

    state = {}
    actions = SimpleNamespace(skip_summarization=False)
    tool_context = SimpleNamespace(state=state, actions=actions)

    result = route_to_phase(
        "audit",
        "The user asked for the audit pre-check.",
        tool_context,
    )

    assert state["classifier_route"] == {
        "route": "audit",
        "rationale": "The user asked for the audit pre-check.",
    }
    assert actions.skip_summarization is True
    assert "audit" in result


def test_classify_router_routes_from_session_state() -> None:
    """Once ADK applies the tool state delta, classify_router must dispatch to
    the selected phase instead of falling back to chat."""
    from app.agents.orchestrator import classify_router

    ctx = _ctx_with_state(
        {
            "classifier_route": {
                "route": "audit",
                "rationale": "The user asked for the audit pre-check.",
            }
        }
    )

    event = classify_router(ctx, None)

    assert event.actions.route == "audit"
    assert event.actions.state_delta == {"current_phase": "audit"}


def test_classify_router_falls_back_to_chat_without_route() -> None:
    """No routing state means the classifier should continue chatting."""
    from app.agents.orchestrator import classify_router

    event = classify_router(_ctx_with_state({}), None)

    assert event.actions.route == "chat"


@pytest.mark.asyncio
async def test_gate_phase4_decision_forces_blocked_when_verdict_is_not_cleared() -> None:
    """Even if the user replies `cleared`, the gate must force `blocked` when
    `phase4_result.cleared_for_audit` is False."""
    from app.agents.orchestrator import gate_phase4_decision

    ctx = _ctx_with_state(
        {
            "phase4_result": {
                "phase": "pre_check",
                "cleared_for_audit": False,
                "schema_errors": ["missing party UUID"],
                "findings_suggestion": [],
                "summary": "SSP fails schema validation.",
            }
        }
    )

    event = await gate_phase4_decision(ctx, "cleared")
    assert event.actions.route == "blocked"


@pytest.mark.asyncio
async def test_gate_phase4_decision_honours_cleared_when_verdict_is_cleared() -> None:
    """When the verdict says cleared and the user replies `cleared`, the
    gate routes to `cleared` (i.e. into Phase 5)."""
    from app.agents.orchestrator import gate_phase4_decision

    ctx = _ctx_with_state(
        {
            "phase4_result": {
                "phase": "pre_check",
                "cleared_for_audit": True,
                "schema_errors": [],
                "findings_suggestion": [],
                "summary": "SSP is audit-ready.",
            }
        }
    )

    event = await gate_phase4_decision(ctx, "cleared")
    assert event.actions.route == "cleared"


@pytest.mark.asyncio
async def test_gate_phase4_decision_blocked_reply_always_blocks() -> None:
    """When the user replies `blocked`, the gate must always route blocked,
    regardless of the underlying verdict."""
    from app.agents.orchestrator import gate_phase4_decision

    ctx = _ctx_with_state(
        {
            "phase4_result": {
                "phase": "pre_check",
                "cleared_for_audit": True,
                "schema_errors": [],
                "findings_suggestion": [],
                "summary": "Looks good.",
            }
        }
    )

    event = await gate_phase4_decision(ctx, "blocked")
    assert event.actions.route == "blocked"


@pytest.mark.asyncio
async def test_gate_phase4_decision_unknown_input_defaults_blocked() -> None:
    """An unrecognised reply defaults to `blocked` — fail safe."""
    from app.agents.orchestrator import gate_phase4_decision

    ctx = _ctx_with_state(
        {
            "phase4_result": {
                "phase": "pre_check",
                "cleared_for_audit": True,
                "schema_errors": [],
                "findings_suggestion": [],
                "summary": "Looks good.",
            }
        }
    )

    event = await gate_phase4_decision(ctx, "yolo")
    assert event.actions.route == "blocked"


# ---------------------------------------------------------------------------
# HITL-resume smoke test — verifies that gate_phaseN_request actually emits
# a RequestInput event the runner would pause on.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gate_phase1_request_yields_request_input() -> None:
    from google.adk.events import RequestInput

    from app.agents.orchestrator import gate_phase1_request

    ctx = _ctx_with_state(
        {
            "phase1_result": {
                "sod_violations": ["ISO == IT-Mgmt"],
                "high_impact_assets": ["asset-uuid-1"],
                "requires_overlay": True,
                "summary": "Two issues found.",
            }
        }
    )

    items = []
    async for item in gate_phase1_request(ctx):
        items.append(item)

    assert len(items) == 1
    assert isinstance(items[0], RequestInput)
    assert items[0].interrupt_id == "gate_phase1"
    assert "Phase 1" in (items[0].message or "")


# ---------------------------------------------------------------------------
# Live LLM test — opt-in
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not os.environ.get("GPP_AGENT_LIVE_TESTS"),
    reason="Live LLM test requires Gemini creds; set GPP_AGENT_LIVE_TESTS=1 to enable.",
)
def test_live_agent_stream() -> None:  # pragma: no cover (opt-in)
    """End-to-end smoke test through `InMemoryRunner`. Requires real ADC and
    reachable MCP backends; not run in default CI."""
    from google.adk.agents.run_config import RunConfig, StreamingMode
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    from app.agent import app as adk_app

    runner = InMemoryRunner(app=adk_app)
    session = runner.session_service.create_session_sync(
        user_id="test_user", app_name=adk_app.name
    )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="I want to do the audit pre-check.")],
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert events, "Expected at least one event from the live workflow run."
