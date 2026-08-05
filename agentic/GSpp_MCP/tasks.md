# Status of GSpp-MCP (v0.1)

## What is Done
- [x] **Standalone Project Structure**: Created `GSpp_MCP` package with separated concerns (server, tools, data, terraform).
- [x] **Catalog Parsing**: Recursive parser in `catalog.py` to handle nested OSCAL groups and sub-controls from the BSI 2023 catalog.
- [x] **Search Engine**: Inverted index and German tokenizer in `search.py` for keyword search across controls.
- [x] **MCP Tool Suite**:
    - `get_control`: Retrieve full control data.
    - `list_controls`: List all controls.
    - `get_group`: Retrieve group metadata.
    - `list_groups`: List all groups.
    - `list_zielobjektkategorien`: List asset categories.
    - `controls_for_zielobjekt`: Retrieve control IDs for a specific category.
    - `search_controls`: Keyword search tool.
- [x] **Infrastructure as Code**:
    - Terraform scripts to enable Cloud Run, Artifact Registry, and IAM.
    - Deployment-ready `Dockerfile`.
- [x] **Terraform Integration**: Scripts use environment variables which are wired to Terraform outputs.
- [x] **Testing**: Unit tests for parser, search, and mapping logic.

## What is Not Done / Upcoming
- [ ] **Roadmap v0.3: Legacy Cross-walk**: Mapping to IT-Grundschutz Edition 2022/2023 (`crosswalk_legacy` tool).
- [ ] **Roadmap v0.4: Profile Resolution**: Implementation of `apply_profile` logic (parameter overrides, alters, includes/excludes).
- [ ] **Roadmap v0.5: Semantic Search**: AI-powered semantic search layer alongside the keyword index.
- [ ] **Complex Zielobjekt Generation**: Replication of the full logic from `stage_profiles.py` within the MCP server (currently relies on static mappings in `zielobjekt_controls.json`).
- [ ] **Automated CI/CD**: GitHub Workflows for automated catalog updates and Cloud Run deployment.
- [ ] **API Gateway/Auth**: Thin proxy for static API key conversion to ID tokens (recommended in README but not implemented in v0.1).
