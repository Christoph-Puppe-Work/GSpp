# DESIGN_SPEC.md

## Overview
**gpp-agent** is a multimodal, AI-supported Multi-Agent System designed to guide users through the entire OSCAL process (Open Security Controls Assessment Language) for BSI Grundschutz++. It features multi-tenant data separation (Mandantenfähigkeit), strict JSON validation for OSCAL artifacts, and an Agent-to-Agent "Maker-Checker" review cycle.

## Architecture & Choices
- **Agent Framework:** ADK (`adk` template)
- **Deployment Target:** Vertex AI Agent Runtime (`agent_runtime`)
- **CI/CD Runner:** Cloud Build (`cloud_build`)
- **Session Storage:** Agent Platform Sessions (managed automatically by Agent Runtime)

## Example Use Cases
1. **Model SSP:** User selects a baseline ISMS and assets; the agent generates the initial OSCAL SSP structure.
2. **Review & Tailoring:** The Reviewer-Agent sub-agent evaluates the generated SSP. The user can manually override the agent's work.
3. **Assessment Plan & Results:** The agent helps map controls to actual implementation states and evaluates BSI compliance.
4. **Save/Load Workspaces:** User commands the agent to save progress. The agent creates a versioned savepoint directly in a specific tenant folder within a GCP Cloud Storage bucket.

## Tools Required
- **MCP Server: `GSpp_MCP`:** Provides access to the "Anwenderkatalog" (BSI catalog).
- **MCP Server: `GS_backend_MCP`:** Provides data persistence capabilities.
- **Tool: `verify_oscal_json`:** Used to rigorously check any generated JSON artifacts against official OSCAL schema files.
- **Tool: GCP Storage Handler:** Custom logic to handle tenant separation and savepoint versioning directly into a GCP Bucket.

## Constraints & Safety Rules
- **Strict Data Isolation:** Different informationsverbund (tenants) must have isolated save directories in GCP.
- **Mandatory Validation:** The agent must never save an OSCAL JSON file without first validating it using `verify_oscal_json`.
- **Human-In-The-Loop (HITL):** The agent must pause and request human approval before making critical state transitions (e.g., finalizing an SSP, starting an assessment).
- **No Direct Schema Edits:** The agent must not edit the core OSCAL schemas themselves, only the generated artifacts.

## Reference Samples
- Similar multi-agent review structures can be found in the `deep-search` ADK sample.
- `adk-ae-oauth` if we eventually need user-level OAuth logic to segregate bucket access.

## Success Criteria
1. Agent can successfully scaffold an SSP and validate it against the BSI schemas.
2. Agent delegates tasks correctly to the Reviewer sub-agent and processes its feedback.
3. Saves are correctly pushed to GCP buckets in the correct tenant/version folder format.
4. Agent successfully interrupts itself to ask the human user for review before proceeding.