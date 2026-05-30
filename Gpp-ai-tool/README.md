# Gpp-ai-tool

Gpp-ai-tool is a Python-based automation framework designed to facilitate the migration from BSI IT-Grundschutz Edition 2023 (Ed2023) to the modernized Grundschutz++ (G++) methodology using OSCAL 1.1.3 profiles.

The tool leverages Google Vertex AI (Gemini) to perform semantic mapping and enrich OSCAL components with AI-generated implementation details.

## Key Features

- **Automated Migration (Mapping):** Maps Ed2023 "Bausteine" to G++ "Zielobjekte" and Ed2023 "Anforderungen" to G++ "Kontrollen".
- **AI-Powered Enrichment:** Generates detailed implementation descriptions for maturity levels 1-5 and performs automated classifications (NIST, ISMS, CIA), emitted as OSCAL `alter` blocks on the generated profiles.
- **Multi-Stage Pipeline:** Modular architecture allowing for individual stage execution or full pipeline runs.
- **Upstream Data Sources:** Reference data (BSI Ed2023 catalog, G++ catalog, target-object categories) is fetched directly from the upstream GitHub repositories; AI enrichment runs on Google Vertex AI (Gemini).

## Installation

### Prerequisites

- Python 3.9 or higher
- Access to a Google Cloud Project with Vertex AI and Cloud Storage enabled
- `gcloud` CLI installed and authenticated

### Setup

1.  **Clone the repository and navigate to the project directory:**
    ```bash
    cd Gpp-ai-tool
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r src/requirements.txt
    ```

## Configuration

The tool is configured via environment variables. Create a `.env` file or export them in your shell:

| Variable | Description | Required |
| :--- | :--- | :--- |
| `GCP_PROJECT_ID` | Your Google Cloud Project ID | Yes |
| `BUCKET_NAME` | GCS bucket for input/output artifacts | Yes |
| `AI_ENDPOINT_ID` | Vertex AI Endpoint ID (or model name) | Yes |
| `REGION` | GCP Region (default: `global`) | No |
| `SOURCE_PREFIX` | GCS path prefix for source files | Yes |
| `OUTPUT_PREFIX` | GCS path prefix for output files | Yes |
| `TEST` | Set to `true` for test mode (default: `false`) | No |
| `MAX_CONCURRENT_AI_REQUESTS` | Limit parallel AI calls (default: `5`) | No |

> **Note:** `BUCKET_NAME`, `SOURCE_PREFIX`, and `OUTPUT_PREFIX` are still validated at startup (the app will refuse to start without them unless `TEST=true`), but the pipeline no longer reads input data from GCS — input catalogs are fetched from GitHub and generated artifacts are written to local directories (`hilfsdateien/`, `Zielobjektkategorien/profile/`, `ED23-Baustein-profile/`) relative to the repository root.

## Usage

### Local Execution

Use the provided helper script to run the pipeline locally:

```bash
./scripts/run_local.sh --stage <stage_name>
```

To run the full pipeline, omit the stage argument:
```bash
./scripts/run_local.sh
```

### Data Sources (Inputs)

All input data is fetched from GitHub at runtime (see `src/constants.py`):

- **G++ catalog** — the Grundschutz++ Kompendium (the target catalog of the migration).
- **BSI Ed2023 catalog** — the source BSI IT-Grundschutz Edition 2023 requirements.
- **`target_object_categories.csv`** — the Zielobjektkategorien (UUID, name, and hierarchy via `ChildOfUUID`).

### Available Pipeline Stages

You can run specific stages using the `--stage` argument. The full pipeline runs them in the order below. Stages 1–2 are deterministic prep/mapping, 3–4 are the AI-driven migration mapping, and 5–6 build and enrich the OSCAL output.

| # | Stage | AI? | What it does |
|---|---|---|---|
| 1 | `stage_strip` | No | Reads the large G++ and BSI JSON catalogs and flattens them into compact markdown tables (`hilfsdateien/*_stripped*.md`), separating controls that target objects from ISMS-level ones. Pre-processing that makes later prompts and lookups manageable. |
| 2 | `stage_gpp` | No | Deterministic mapping: walks the G++ catalog and the Zielobjektkategorien CSV (including the parent hierarchy) to compute, for each Zielobjekt, the set of applicable G++ controls. Writes `hilfsdateien/zielobjekt_controls.json`. |
| 3 | `stage_match_bausteine` | **Yes** | For each BSI Baustein, asks the model which G++ Zielobjekt it corresponds to (title + description → best match). Writes the Baustein→Zielobjekt map (`hilfsdateien/baustein_zielobjekt.json`). |
| 4 | `stage_matching` | **Yes** | The precise 1:1 migration step: for each Baustein/Zielobjekt pair, maps individual BSI *Anforderungen* to individual G++ *controls* semantically. Writes `hilfsdateien/controls_anforderungen.json`. |
| 5 | `stage_profiles` | No | Generates the **base OSCAL profiles** — one per Zielobjekt — each importing the G++ catalog and including that Zielobjekt's controls. Output is split into `Zielobjektkategorien/profile/regular/` and `…/process/` (Methodik and `*_prozesse`). |
| 6 | `stage_profiles_enhanced` | **Yes** | Takes the base profiles and, using the BSI Ed2023 requirement text from the matching, generates maturity-level statements (levels 1–5) plus classifications (NIST class, ISMS phase, CIA) as OSCAL `alter` blocks. Writes the per-Baustein enhanced profiles to `ED23-Baustein-profile/` as `[Zielobjektkategorie]_[Baustein-ID]_[Baustein-Name].json`. |

#### Data flow

```
catalogs + CSV (GitHub)
        │
  1 strip ──► markdown tables (context)
  2 gpp   ──► zielobjekt_controls.json        (Zielobjekt → G++ controls)        [deterministic]
  3 match_bausteine ──► baustein_zielobjekt.json    (Baustein → Zielobjekt)      [AI]
  4 matching ──► controls_anforderungen.json  (BSI Anforderung → G++ control)    [AI]
        │
  5 profiles ──► base profiles (import G++ catalog)   Zielobjektkategorien/profile/{regular,process}/
        │
  6 profiles_enhanced ──► enriched profiles (+ alter blocks)   ED23-Baustein-profile/   [AI]
```

### Running a single stage locally

To (re)generate the G++ Zielobjektkategorien and process profiles locally:

```bash
./scripts/run_local.sh --stage stage_profiles
```

To then enrich them with the BSI Ed2023 maturity statements:

```bash
./scripts/run_local.sh --stage stage_profiles_enhanced
```

The same pattern works for any stage name listed above (e.g. `--stage stage_matching`). `run_local.sh` sets `OVERWRITE_TEMP_FILES=true` so existing profiles are regenerated; pass `--clear-all` to first wipe the generated output directories.

## Deployment

The tool is designed to run as a Google Cloud Run Job. Use the deployment script:

```bash
./scripts/deploy.sh <GCP_PROJECT_ID> <GCP_REGION>
```

## How-To / Workflow

1.  **Preparation:** No manual upload is required — the source BSI Ed2023 catalog, the G++ catalog, and the target-object categories are fetched directly from their upstream GitHub repositories at runtime (see `src/constants.py`).
2.  **Mapping:** The tool first establishes a 1:1 mapping between old blocks and new target objects.
3.  **Matching:** AI analyzes the semantic meaning of requirements to find the best-fitting G++ control.
4.  **Enrichment:** For each matched control, Gemini generates implementation guidance and maturity level descriptions based on the original BSI context.
5.  **Finalization:** The tool outputs valid OSCAL 1.1.3 profiles (enriched with `alter` blocks) ready for use in G++ compatible tools.

---

For more technical details, refer to [G++ Automatisierte Erstellung Zielobjekte-Bausteine.md](./G++%20Automatisierte%20Erstellung%20Zielobjekte-Bausteine.md).
