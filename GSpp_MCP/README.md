# BSI Grundschutz++ MCP Server

Read-only MCP server that exposes the BSI Anwenderkatalog Grundschutz++ as a
small, intent-shaped tool surface for LLM agents. Designed to run as a single
container on Google Cloud Run and act as the back office for the
[Grundschutz++ One-Page-Apps](https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/tree/main/One-Page-Apps)
as they transition from browser-only tools into agentic workflows.

> Status: early. Catalog parsing and core tools first. Profile resolution and
> SSP-authoring helpers come later, when the agent-side actually needs them.

## Why this exists

The One-Page-Apps currently embed (or fetch) the catalog client-side and ship
all logic in the browser. That works for hand-driven authoring but breaks down
for agents, which need:

- a stable, versioned source of truth for `BER.1.1`-style requirement IDs,
- queries shaped by intent (`get_control`, `search_controls`) rather than
  full-tree downloads of the JSON,
- parameter resolution and modal-verb (`MUSS`/`SOLLTE`) awareness without
  re-implementing the Grundschutz++ semantics in every prompt,
- token-efficient responses — a naive agent that pulls the whole catalog into
  context will burn tokens on irrelevant requirements.

This server gives agents the catalog as a tool, not as a file.

## Catalog source of truth

- File:
  `Anwenderkataloge/Grundschutz++/Grundschutz++-catalog.json` from
  `BSI-Bund/Stand-der-Technik-Bibliothek` (`main` branch).
- Format: OSCAL 1.1.x catalog (JSON).
- License: CC BY-SA 4.0 — attribution and share-alike apply to any
  derivative output, including agent responses that paraphrase requirement
  text. The server emits a `_attribution` field on every response.
- The catalog is **baked into the container image** at build time, not fetched
  at runtime. Reproducible builds, no GitHub-rate-limit surprises during a cold
  start, and deterministic image hashes for audit trails.

A scheduled GitHub Action rebuilds and redeploys the image when BSI publishes
a new commit on the catalog path (see `.github/workflows/catalog-watch.yml`).

## Grundschutz++ specifics worth knowing

A generic OSCAL server would miss what makes G++ usable:

- **Modalverb namespace.** Each requirement carries a `modalverb` property
  (`MUSS`, `SOLLTE`) drawn from the BSI namespace CSV. The server exposes this
  as a first-class filter on `list_controls` and `search_controls`.
- **Stufen / Leistungszahlen.** G++ replaced the old Basis / Standard /
  Erhöhter-Schutzbedarf trichotomy with dynamic thresholds. The `stufen`
  namespace property is preserved on every control and queryable.
- **Zielobjektkategorien.** Controls are scoped to standardized asset
  categories. `list_zielobjektkategorien` and `controls_for_zielobjekt` are
  separate tools because asset-to-control mapping is the most common agent
  query and deserves its own surface.
- **German prose.** No translation, no normalization. Search is German-aware
  (lowercase, Umlaut folding, `ß → ss`, German stop-words removed).

## MCP tool surface

Minimum useful set, all read-only:

| Tool | Purpose |
| --- | --- |
| `catalog_info` | Metadata block, OSCAL version, last-modified, control count |
| `list_groups` | Group hierarchy (IDs, titles, control counts) |
| `list_controls` | IDs + titles only, filterable by group, modalverb, stufe |
| `get_control` | Full control; opt-in expansion of statement, params, links |
| `search_controls` | Ranked IDs from an in-memory inverted index |
| `get_parameter` | Parameter definition + select values |
| `find_referencing_controls` | Backrefs from a control ID |
| `list_zielobjektkategorien` | Asset categories defined by the catalog |
| `controls_for_zielobjekt` | Controls applicable to an asset category |

Stubbed for later, returning `not-implemented`:

- `apply_profile(profile_uri)` — profile resolution with param overrides,
  alters, includes/excludes. Real subsystem; deferred until an agent needs it.
- `diff_catalog(version_a, version_b)` — version-to-version delta, useful when
  BSI ships a new edition.

No write tools. SSP authoring, profile creation and assessment-result
emission belong in separate MCP servers with their own permission model.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Cloud Run service: gs-plus-plus-mcp                             │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐     │
│   │  FastMCP app (Python 3.12)                             │     │
│   │   - Streamable HTTP transport on $PORT                 │     │
│   │   - Catalog parsed on cold start (~1–2s)               │     │
│   │   - In-memory: controls_by_id, groups_by_id,           │     │
│   │     params_by_id, inverted_index, backrefs             │     │
│   │   - JSON-schema validated on load (fail-fast)          │     │
│   └────────────────────────────────────────────────────────┘     │
│                          ▲                                       │
│                          │                                       │
│   /mcp (POST, streaming) │ Bearer ID token (Cloud Run IAM)       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
   One-Page-Apps                       Other MCP-aware
   (becoming agents)                   agents / IDEs / pipelines
```

- **Transport.** Streamable HTTP. SSE-only is deprecated in the current MCP
  spec; Cloud Run handles long-lived streaming responses fine but caps a
  single request at 60 minutes by default — adequate for catalog queries.
- **State.** Stateless beyond the parsed catalog. No DB, no Redis. A second
  instance (Cloud Run autoscaler) holds its own copy. ~50 MB resident at
  baseline; Cloud Run minimum (256 MiB) is enough but the service is
  configured for 512 MiB to leave room for the inverted index.
- **Cold start.** Aim for < 3 seconds end-to-end. Catalog is loaded eagerly
  in the module import, not lazily on first request, so the first call after
  a scale-from-zero is not penalized.

## Repository layout

```
.
├── README.md
├── pyproject.toml
├── Dockerfile
├── server/
│   ├── __init__.py
│   ├── main.py              # FastMCP entrypoint, tool registration
│   ├── catalog.py           # parse + index the OSCAL JSON
│   ├── search.py            # inverted index, German tokenizer
│   ├── tools/
│   │   ├── controls.py
│   │   ├── groups.py
│   │   ├── params.py
│   │   ├── search.py
│   │   └── zielobjekte.py
│   └── schemas/
│       └── oscal-catalog-1.1.2.json
├── data/
│   └── Grundschutz++-catalog.json   # baked in at build time
├── tests/
│   ├── test_catalog.py
│   ├── test_search.py
│   └── fixtures/
│       └── mini-catalog.json
└── .github/
    └── workflows/
        ├── ci.yml
        └── catalog-watch.yml
```

## Local development

Prerequisites: Python 3.12, `uv` (or `pip`), `gcloud` CLI configured for the
target project.

```bash
# Pull the catalog into ./data
make fetch-catalog

# Install deps
uv sync

# Run the server locally on http://localhost:8080/mcp
uv run python -m server.main

# Run the test suite
uv run pytest
```

Smoke test against a local server with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector http://localhost:8080/mcp
```

## Cloud Run deployment

Two deployment paths. Pick one and stick with it.

### Option A — `gcloud run deploy --source` (fast)

```bash
PROJECT_ID=your-gcp-project
REGION=europe-west3                  # Frankfurt; data residency for BSI

gcloud run deploy gs-plus-plus-mcp \
  --project       $PROJECT_ID \
  --region        $REGION \
  --source        . \
  --memory        512Mi \
  --cpu           1 \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency   80 \
  --port          8080 \
  --no-allow-unauthenticated \
  --service-account gs-mcp-runtime@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars  CATALOG_PATH=/app/data/Grundschutz++-catalog.json
```

`--source` builds the image with Cloud Build using the included `Dockerfile`.

### Option B — Artifact Registry + explicit image (auditable)

```bash
gcloud builds submit \
  --tag europe-west3-docker.pkg.dev/$PROJECT_ID/mcp/gs-plus-plus-mcp:$(git rev-parse --short HEAD)

gcloud run deploy gs-plus-plus-mcp \
  --image europe-west3-docker.pkg.dev/$PROJECT_ID/mcp/gs-plus-plus-mcp:$(git rev-parse --short HEAD) \
  ...
```

Image tags pinned to git SHAs make rollbacks trivial and give you a clean
audit trail (relevant if a customer ever asks which catalog revision an
agent answer was based on).

### Region

Use `europe-west3` (Frankfurt) or `europe-west4` (Eemshaven) for EU data
residency. BSI material under CC BY-SA 4.0 has no residency requirement, but
operating EU-only avoids unrelated questions during customer audits.

## Authentication

Default: **Cloud Run IAM only** (`--no-allow-unauthenticated`). Callers
present a Google-issued ID token for the service account, validated by Cloud
Run before the request reaches the container.

For agent clients that can't easily mint Google ID tokens (browser-side
One-Page-Apps, third-party agent runtimes), put a thin proxy in front:

- **Recommended:** API Gateway or a small Cloud Run sidecar that converts a
  static API key (held in Secret Manager) into an ID token via the metadata
  server. Keeps key rotation server-side; the catalog server stays IAM-only.
- **Avoid:** `--allow-unauthenticated` plus an in-app API key check. Anyone
  who finds the URL can still hammer the service and rack up egress.

The MCP spec's own OAuth flow is improving but client support is uneven; the
gateway pattern is the safe path through the next year.

## Catalog updates

Catalog refreshes are version events, not background reloads.

```yaml
# .github/workflows/catalog-watch.yml (sketch)
on:
  schedule: [{ cron: "0 6 * * *" }]    # daily 06:00 UTC
  workflow_dispatch:

jobs:
  check-and-deploy:
    steps:
      - uses: actions/checkout@v4
      - name: Fetch upstream catalog
        run: curl -fsSL "$BSI_RAW_URL" -o data/Grundschutz++-catalog.json
      - name: Detect change
        id: diff
        run: |
          git diff --quiet data/ || echo "changed=true" >> $GITHUB_OUTPUT
      - name: Open PR with new catalog
        if: steps.diff.outputs.changed == 'true'
        uses: peter-evans/create-pull-request@v6
```

A human reviews the diff (BSI sometimes restructures groups across editions)
and merges. CI then builds, tests, and rolls out a new revision. Cloud Run
keeps the previous revision warm for instant rollback.

## Observability

- **Logs.** Structured JSON to stdout (Cloud Run captures it as Cloud
  Logging entries). Each tool invocation logs `tool`, `args_hash`,
  `latency_ms`, `result_size_bytes`. No control bodies in logs.
- **Metrics.** Cloud Monitoring captures request count, latency, container
  CPU/memory automatically. A custom log-based metric tracks
  `tool_invocations` per tool name — useful for spotting which agent paths
  are actually being used.
- **Tracing.** OpenTelemetry exporter to Cloud Trace, sampled at 5%.
- **Health.** `GET /healthz` returns 200 once the catalog has parsed and
  the index has built. Cloud Run uses this as the startup probe.

## Threat model in one paragraph

The catalog is public, so confidentiality is not the point. The risks are:
(1) availability — an agent loop hammering `search_controls` at high
concurrency; mitigated by Cloud Run's per-instance concurrency cap and
`max-instances`. (2) integrity — a tampered catalog leading to wrong agent
answers; mitigated by baking the catalog into the image, recording the
upstream SHA in `catalog_info`, and signing images with Binary Authorization
in projects that require it. (3) excess egress — large `get_control` results
amplifying token spend; mitigated by lean default expansion and explicit
opt-in for enhancements.

## Roadmap

- [ ] **v0.1** — read-only tools above, deployed on Cloud Run, called by
      one One-Page-App (Blaupausen-Generator) as proof of contract.
- [ ] **v0.2** — `controls_for_zielobjekt` + `list_zielobjektkategorien`,
      driven by the asset-mapping flow in the SSP authoring app.
- [ ] **v0.3** — cross-walk to legacy IT-Grundschutz Edition 2023
      (`crosswalk_legacy(control_id)`); the mapping CSV from the Methodik
      catalog feeds this.
- [ ] **v0.4** — `apply_profile`. Done correctly (param overrides, alters,
      includes/excludes), not as a `JSON.parse` shortcut.
- [ ] **v0.5** — optional semantic search layer alongside the keyword index,
      for cross-framework mapping (CIS / ISO 27001 Annex A → G++).

Out of scope, intentionally: write tools, multi-tenant catalog hosting,
embedded LLM calls inside the server. This is plumbing, not a product.

## License & attribution

- Server code: Apache-2.0 (see `LICENSE`).
- Catalog data under `data/`: © Bundesamt für Sicherheit in der
  Informationstechnik (BSI), licensed CC BY-SA 4.0. Source:
  `BSI-Bund/Stand-der-Technik-Bibliothek`. Any agent answer derived from
  catalog content inherits the share-alike obligation; the server returns
  a machine-readable `_attribution` block on every response so downstream
  systems can carry the notice.

## Maintainer

Christoph Puppe — Principal Enterprise Security Architect, NTT DATA
Deutschland. Co-author of IT-Grundschutz-Kompendium modules APP.4.4
(Kubernetes) and SYS.1.6 (Containerisierung); contributor to IT-Grundschutz++.
