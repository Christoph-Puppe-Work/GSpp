# Skills: Writing a Grundschutz++ MCP Server

This document outlines the specialized skills and best practices required to build and maintain a Model Context Protocol (MCP) server for BSI Grundschutz++.

## 1. Core OSCAL Proficiency
*   **Hierarchical Parsing**: Ability to traverse deeply nested OSCAL `groups` (e.g., `main-group` -> `baustein`) and `controls` (which can contain nested sub-controls).
*   **ID Stability**: Relying on stable identifiers like `BER.1.1` for requirements rather than transient array indices.
*   **Metadata Extraction**: Correctly identifying `parts` (prose, guidance) and `props` (modal verbs, implementation levels) within the OSCAL structure.

## 2. Intent-Shaped Tool Design
*   **Query vs. Download**: Designing tools that answer specific agent questions (`get_control`, `search_controls`) rather than requiring the agent to download and parse the entire catalog.
*   **Token Efficiency**: Providing "slim" versions of controls by default to conserve the agent's context window. Only return full raw OSCAL JSON via dedicated "raw" tools when explicitly needed.
*   **Domain-Specific Access**: Exposing Grundschutz++ specific mappings, such as `controls_for_zielobjekt`, to bridge the gap between asset management and security requirements.

## 3. Search & Information Retrieval
*   **German-Aware Tokenization**: Implementing search indices that handle German specifics (case-insensitivity, stop-word removal, umlauts) since Grundschutz++ content is primary German.
*   **In-Memory Indexing**: Building and maintaining in-memory inverted indices for sub-second keyword search across thousands of requirements.

## 4. Lifecycle & Performance
*   **Eager Loading**: Parsing the catalog and building indices during the server's cold start to ensure immediate responsiveness to tool calls.
*   **Baking Data**: Including the catalog source of truth in the container image at build time for reproducibility and to avoid runtime dependency on external APIs.

## 5. Security & Deployment
*   **IAM-First Access**: Enforcing restricted access using Cloud IAM (e.g., `--no-allow-unauthenticated` on Cloud Run) to protect the service while keeping it accessible to authorized agents.
*   **Stateless Scaling**: Designing the server to be horizontally scalable by keeping all state (the parsed catalog) immutable within each instance.

## 6. Validation & Quality
*   **Schema Enforcement**: Validating OSCAL structures against official BSI schemas to ensure the integrity of the data being served and processed.
*   **Attribution**: Ensuring that responses include machine-readable attribution (e.g., `_attribution` block) as required by the CC BY-SA 4.0 license.

## Best Practices Summary
1.  **Never serve the whole file**: Always use targeted tool responses.
2.  **Abstract OSCAL complexity**: Don't force the agent to understand the OSCAL schema unless necessary.
3.  **Use human-readable metadata**: Enrich UUIDs with human-readable names from auxiliary data (e.g., `zielobjektkategorien.csv`).
4.  **Prioritize read-only access**: Keep the catalog server separate from state-modifying tools (like SSP authoring) for better security boundaries.
