# Grundschutz++ (G++) AI Tool

Welcome to the **Grundschutz++ AI Tool**. This application provides an automated, AI-driven pipeline for generating [OSCAL 1.1.3](https://pages.nist.gov/OSCAL/) Component Definitions. 

Its primary purpose is to facilitate the migration from the traditional, module-based **BSI IT-Grundschutz Edition 2023 (Ed2023)** to the modernized, data-centric, and inheritance-driven **Grundschutz++ (G++)** methodology.

By leveraging Python and Google Cloud Vertex AI (Gemini), this tool maps old BSI requirements to new G++ controls and enriches them with detailed, AI-generated implementation guidance across different maturity levels.

## Features

- **Automated Mapping:** Intelligently maps legacy BSI *Bausteine* (modules) to G++ *Zielobjekte* (target objects), and specifically maps individual BSI *Anforderungen* (requirements) to G++ *Kontrollen* (controls) using a strict 1:1 relationship.
- **Contextual Enrichment:** Uses Gemini AI to generate rich implementation details, including detailed statements, guidance, and assessment methods for maturity levels 1-5.
- **Classification:** Automatically assigns relevant metadata such as NIST Class, ISMS Phase, and CIA Impact to the newly mapped controls.
- **OSCAL Generation:** Outputs standards-compliant OSCAL profiles and component definitions for seamless integration into modern GRC (Governance, Risk, and Compliance) tools.
- **Asynchronous Execution:** Highly parallelized architecture for fast processing using robust retry mechanisms and error handling.

## Pipeline Architecture

The application operates as a multi-stage data processing pipeline. Each stage is designed to complete a specific part of the migration and enrichment process.

### The 6 Stages of Processing

1. **Stage: Strip (`stage_strip`)**
   - **Purpose:** Prepares the input data.
   - **Action:** Cleans and converts source documents (like BSI compendiums and G++ definitions) into clean Markdown format. This provides the optimal context for the AI models in later stages.

2. **Stage: GPP (`stage_gpp`)**
   - **Purpose:** Establishes the target baseline.
   - **Action:** Deterministically processes the G++ compendium to build a hierarchy of controls. It figures out the full pool of available G++ controls applicable to each specific *Zielobjekt* based on inheritance rules.

3. **Stage: Match Bausteine (`stage_match_bausteine`)**
   - **Purpose:** High-level migration mapping.
   - **Action:** Uses AI to semantically map each relevant BSI Ed2023 *Baustein* to exactly one appropriate G++ *Zielobjekt*.

4. **Stage: Matching (`stage_matching`)**
   - **Purpose:** Detailed migration mapping.
   - **Action:** For every BSI *Anforderung* within a mapped *Baustein*, the AI determines the single most appropriate G++ *Kontrolle*. This search is strictly limited to the control pool established in `stage_gpp` for the target *Zielobjekt*, ensuring highly accurate, context-aware 1:1 mapping.

5. **Stage: Profiles (`stage_profiles`)**
   - **Purpose:** Generate intermediary OSCAL structures.
   - **Action:** Deterministically creates an OSCAL Profile for each *Zielobjekt*. These profiles contain references to all the applicable G++ controls required.

6. **Stage: Component Generation (`stage_component`)**
   - **Purpose:** AI Enrichment and final output generation.
   - **Action:** This is the most intensive stage. The AI (Gemini Pro) ingests the matched G++ controls and the contextual background of the original BSI Baustein. It then generates comprehensive OSCAL Component Definitions. This includes writing detailed implementation prose for Maturity Levels 1 through 5 (Statement, Guidance, Assessment) and determining standard classifications (NIST, ISMS, CIA). 

*Note: The generated components are based on the full profile of the Zielobjekt (from Stage 2), meaning they provide a complete control implementation framework, contextualized by the migrated BSI data.*

## Prerequisites

To run this tool, you will need:

- **Python 3.10+**
- **Google Cloud Platform (GCP) Account** with Vertex AI API enabled.
- **GCP Credentials:** Set up via `gcloud auth application-default login` or by setting the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.
- Required Python packages (install via `pip install -r requirements.txt`).

## Usage

The application is orchestrated via a command-line interface. You can run the entire pipeline from start to finish, or execute individual stages.

### Running the Full Pipeline

To execute all stages sequentially:

```bash
python src/main.py
```

### Running a Specific Stage

If you need to re-run a specific part of the process (e.g., during testing or debugging), you can specify the `--stage` argument:

```bash
# Example: Run only the Baustein matching stage
python src/main.py --stage stage_match_bausteine

# Available stages:
# stage_strip, stage_gpp, stage_match_bausteine, stage_matching, stage_profiles, stage_component
```

## Known Limitations

Please review `issues.md` for a detailed breakdown of current architectural constraints and AI generation considerations, such as the strict 1:1 mapping limitation and potential output variability due to AI temperature settings.
