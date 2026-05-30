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

### Available Pipeline Stages

You can run specific stages using the `--stage` argument. The full pipeline runs them in this order:

- `stage_strip`: Pre-processes and cleans source data.
- `stage_gpp`: Determines applicable G++ controls for target objects.
- `stage_match_bausteine`: Maps BSI Bausteine to G++ Zielobjekte.
- `stage_matching`: Performs semantic matching of requirements to controls.
- `stage_profiles`: Generates the base OSCAL profiles from the G++ Zielobjektkategorien (target-object categories) and process Bausteine. Each profile imports the G++ catalog and includes the controls mapped to that target object. Output is split into:
  - `Zielobjektkategorien/profile/regular/<name>_profile.json` — regular Zielobjektkategorien.
  - `Zielobjektkategorien/profile/process/<name>_process_profile.json` — process profiles (Methodik and `*_prozesse`).
- `stage_profiles_enhanced`: Enriches the base profiles with AI-generated maturity-level statements (OSCAL `alter` blocks) derived from the BSI Ed2023 catalog. Output is written to `ED23-Baustein-profile/`.

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
