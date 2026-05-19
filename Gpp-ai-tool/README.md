# Gpp-ai-tool

Gpp-ai-tool is a Python-based automation framework designed to facilitate the migration from BSI IT-Grundschutz Edition 2023 (Ed2023) to the modernized Grundschutz++ (G++) methodology using OSCAL 1.1.3 component definitions.

The tool leverages Google Vertex AI (Gemini) to perform semantic mapping and enrich OSCAL components with AI-generated implementation details.

## Key Features

- **Automated Migration (Mapping):** Maps Ed2023 "Bausteine" to G++ "Zielobjekte" and Ed2023 "Anforderungen" to G++ "Kontrollen".
- **AI-Powered Enrichment:** Generates detailed implementation descriptions for maturity levels 1-5 and performs automated classifications (NIST, ISMS, CIA).
- **Multi-Stage Pipeline:** Modular architecture allowing for individual stage execution or full pipeline runs.
- **Robust Integration:** Built-in support for Google Cloud Storage and Vertex AI.

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

## Usage

### Local Execution

Use the provided helper script to run the pipeline locally:

```bash
./scripts/run_local.sh [stage_name]
```

To run the full pipeline, omit the stage name:
```bash
./scripts/run_local.sh
```

### Available Pipeline Stages

You can run specific stages using the `--stage` argument:

- `stage_strip`: Pre-processes and cleans source data.
- `stage_gpp`: Determines applicable G++ controls for target objects.
- `stage_match_bausteine`: Maps BSI Bausteine to G++ Zielobjekte.
- `stage_matching`: Performs semantic matching of requirements to controls.
- `stage_profiles`: Generates OSCAL profiles.
- `stage_component`: Generates the final enriched OSCAL component definitions.

## Deployment

The tool is designed to run as a Google Cloud Run Job. Use the deployment script:

```bash
./scripts/deploy.sh <GCP_PROJECT_ID> <GCP_REGION>
```

## How-To / Workflow

1.  **Preparation:** Upload your source BSI Ed2023 artifacts and G++ reference data to the configured GCS bucket.
2.  **Mapping:** The tool first establishes a 1:1 mapping between old blocks and new target objects.
3.  **Matching:** AI analyzes the semantic meaning of requirements to find the best-fitting G++ control.
4.  **Enrichment:** For each matched control, Gemini generates implementation guidance and maturity level descriptions based on the original BSI context.
5.  **Finalization:** The tool outputs valid OSCAL 1.1.3 JSON files ready for use in G++ compatible tools.

---

For more technical details, refer to [G++ Automatisierte Erstellung Zielobjekte-Bausteine.md](./G++%20Automatisierte%20Erstellung%20Zielobjekte-Bausteine.md).
