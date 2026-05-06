# Implementation Plan: G++ OSCAL Context- und State-Manager (MCP Server)

This document outlines the phased implementation plan for the G++ OSCAL Context Management MCP Server deployed on GCP Cloud Run.

## Phase 1: Infrastructure & Deployment (Terraform)
- [ ] Set up Terraform project structure for GCP Cloud Run deployment.
- [ ] Define Cloud Run service resource with:
  - Port injection (`PORT` env var).
  - Environment variables for GCP project, bucket name, etc.
- [ ] Configure deployment process to build and push the Docker image to Artifact Registry using `uv` (as per the skill file).
- [ ] Ensure the container service binds to `0.0.0.0` and uses the `python:3.13-slim` base image.

## Phase 2: Backend Connection (GCP Storage)
- [ ] Set up GCP Cloud Storage bucket for tenant (IV) data isolation.
- [ ] Implement a `storage` module to handle GCP Bucket I/O operations.
- [ ] Ensure the MCP Server is the *only* entity configured to access the GCP bucket directly.
- [ ] Create functions for writing/reading files to/from tenant-specific paths (using the `iv_id` as the folder prefix/namespace).

## Phase 3: Authentication (Google Machine Identities)
- [ ] Configure IAM roles for the Cloud Run service account.
- [ ] Set up authentication for the Agent to access the MCP server using `roles/run.invoker`.
- [ ] Ensure the Agent invokes the MCP Server using GCP Service Account / OIDC tokens (Google Machine Identities).
- [ ] Implement the `get_iv_id` extraction logic in the MCP server to enforce multi-tenancy:
  - Extract the `iv_id` securely from the `Context` (`ctx.request_context.session.user_id`).
  - Expect the format: `{caller}::iv::{iv_id}`.

## Phase 4: Artifact Creation (Initialization & Validation)
- [ ] Initialize the FastMCP server skeleton with the 8 hardcoded `OscalModel` enums.
- [ ] Pre-load the 8 NIST OSCAL 1.2.2 JSON schemas into memory (RAM) at startup for Zero-Trust local validation.
- [ ] Implement the `create_oscal_model` tool:
  - Generate the initial JSON document based on agent payload.
  - Perform local air-gapped `jsonschema` validation against the pre-loaded schemas.
  - Add necessary OSCAL 1.2.2 metadata (UUIDs, Timestamps).
  - Write the successful draft as an initial snapshot (e.g., `save_v1.json`) to GCP Storage.

## Phase 5: Reading (Extractors & Profile Resolution)
- [ ] Implement read tools to return isolated, pre-filtered fragments (preventing the "Lost-in-the-Middle" LLM effect):
  - **SSP:** `get_ssp_inventory`, `get_ssp_implementation`.
  - **Assessment (AP & AR):** `get_assessment_subjects`, `get_assessment_controls`, `get_assessment_findings`.
  - **POA&M:** `get_poam_items`.
- [ ] Implement the **Profile Resolution Engine**:
  - Load the base BSI Catalog (local cache).
  - Resolve `alter` and `set-parameter` directives from the Profile.
  - Implement RAM caching with invalidation based on the SHA-256 hash of the Profile snapshot.

## Phase 6: Manipulating (Maker-Checker Loop & Snapshots)
- [ ] Implement the `update_oscal_model` tool for state mutation.
- [ ] Implement the In-Memory Transaction Loop:
  - **Draft Phase:** Fetch the last valid snapshot from GCP, merge the patch/update into the JSON tree in RAM.
  - **Validation Phase:** Validate the entire RAM draft against the local schema.
  - **Commit Phase:** If valid, save the result as a new snapshot version (e.g., `save_v2.json`) to GCP. Do NOT overwrite existing snapshots.
- [ ] Implement Maker-Checker feedback:
  - If validation fails, explicitly raise `jsonschema.ValidationError` with the exact stack trace and JSON path so the Agent can correct its payload.
