# Implementation Plan: G++ OSCAL Context- und State-Manager (MCP Server)

This document outlines the phased implementation plan for the G++ OSCAL Context Management MCP Server deployed on GCP Cloud Run.

## Phase 1: Infrastructure & Deployment (Terraform)
- [x] Set up Terraform project structure for GCP Cloud Run deployment.
- [x] Define Cloud Run service resource with:
  - Port injection (`PORT` env var).
  - Environment variables for GCP project, bucket name, etc.
- [x] Configure deployment process to build and push the Docker image to Artifact Registry using `uv` (as per the skill file).
- [x] Ensure the container service binds to `0.0.0.0` and uses the `python:3.13-slim` base image.

## Phase 2: Backend Connection (GCP Storage)
- [x] Set up GCP Cloud Storage bucket for tenant (IV) data isolation.
- [x] Implement a `storage` module to handle GCP Bucket I/O operations.
- [x] Ensure the MCP Server is the *only* entity configured to access the GCP bucket directly.
- [x] Create functions for writing/reading files to/from tenant-specific paths (using the `iv_id` as the folder prefix/namespace).

## Phase 3: Authentication (Google Machine Identities)
- [x] Configure IAM roles for the Cloud Run service account.
- [x] Set up authentication for the Agent to access the MCP server using `roles/run.invoker`.
- [x] Ensure the Agent invokes the MCP Server using GCP Service Account / OIDC tokens (Google Machine Identities).
- [x] Implement the `get_iv_id` extraction logic in the MCP server to enforce multi-tenancy:
  - Extract the `iv_id` securely from the `Context` (`ctx.request_context.session.user_id`).
  - Expect the format: `{caller}::iv::{iv_id}`.

## Phase 4: Artifact Creation (Initialization & Validation)
- [x] Initialize the FastMCP server skeleton with the 8 hardcoded `OscalModel` enums.
- [x] Pre-load the 8 NIST OSCAL 1.2.2 JSON schemas into memory (RAM) at startup for Zero-Trust local validation.
- [x] Implement the `create_oscal_model` tool:
  - [x] Generate the initial JSON document based on agent payload.
  - [x] Perform local air-gapped `jsonschema` validation against the pre-loaded schemas.
  - [x] Add necessary OSCAL 1.2.2 metadata (UUIDs, Timestamps).
  - [x] Write the successful draft as an initial snapshot (e.g., `save_v1.json`) to GCP Storage.

## Phase 5: Reading (Extractors & Profile Resolution)
- [ ] Implement read tools to return isolated, pre-filtered fragments (preventing the "Lost-in-the-Middle" LLM effect):
  - [ ] **SSP:** `get_ssp_inventory`, `get_ssp_implementation` (add `role_id` filter).
  - [ ] **Assessment (AP & AR):** `get_assessment_subjects` (correctly use AP/AR), `get_assessment_controls` (add `selected_only`, resolve UUIDs to SSP names), `get_assessment_findings`.
  - [x] **POA&M:** `get_poam_items`.
- [ ] Implement the **Profile Resolution Engine**:
  - [x] Load the base BSI Catalog (local cache).
  - [x] Resolve `alter` and `set-parameter` directives from the Profile. (Simplified implementation)
  - [x] Implement RAM caching with invalidation based on the SHA-256 hash of the Profile snapshot.
  - [ ] **BSI Local Resolution:** Automatically load the baked-in BSI catalog when a profile references the BSI GitHub URI in its `href`.

## Phase 6: Manipulating (Maker-Checker Loop & Snapshots)
- [x] Implement the `update_oscal_model` tool for state mutation.
- [x] Implement the In-Memory Transaction Loop:
  - [x] **Draft Phase:** Fetch the last valid snapshot from GCP, merge the patch/update into the JSON tree in RAM.
  - [x] **Validation Phase:** Validate the entire RAM draft against the local schema.
  - [x] **Commit Phase:** If valid, save the result as a new snapshot version (e.g., `save_v2.json`) to GCP. Do NOT overwrite existing snapshots.
- [x] Implement Maker-Checker feedback:
  - [x] If validation fails, explicitly raise `jsonschema.ValidationError` with the exact stack trace and JSON path so the Agent can correct its payload.

## Phase 7: Extended Artifact Management & Snapshots
- [ ] Implement `list_oscal_models`: Tool to list all initialized models for a tenant.
- [ ] Implement `get_oscal_model_raw`: Tool to retrieve the full original JSON content (with version support).
- [ ] Implement `list_oscal_model_versions`: Tool to list all available snapshot versions for a specific model.
