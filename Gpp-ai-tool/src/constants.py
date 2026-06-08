"""
Defines application-wide constants.

This module centralizes all static, non-configurable values used across the
application. This improves maintainability by providing a single, authoritative
source for these constants.
"""

import os
import re

# --- Path Configuration ---
# All paths are resolved as absolute paths to ensure the application runs
# correctly regardless of the current working directory.
SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
# REPO_ROOT is the parent directory of the 'Gpp-ai-tool' project folder. It can be
# overridden with OUTPUT_ROOT so the generated artifacts can be written somewhere other
# than the repository's sibling-directory layout (issue 3.5).
REPO_ROOT = os.path.abspath(os.path.join(SRC_ROOT, "..", ".."))
OUTPUT_ROOT = os.path.abspath(os.environ.get("OUTPUT_ROOT", REPO_ROOT))

# ANFORDERUNG_ID_PATTERN = re.compile(r"^[A-Z]{2,}(\.\d+)+(?:.A\d+)?$")
ANFORDERUNG_ID_PATTERN = re.compile(r"^.*$")

# --- Data Source URLs ---
# Input data is fetched directly from the upstream GitHub repositories (raw
# content) rather than from local submodule checkouts. The loaders in
# utils/data_loader.py and utils/file_utils.py transparently download these.
ZIELOBJEKTKATEGORIEN_CSV_PATH = "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/refs/heads/main/Dokumentation/namespaces/target_object_categories.csv"
BSI_2023_JSON_PATH = "https://raw.githubusercontent.com/NTTDATA-DACH/BSI-GS-Benutzerdefinierte-Edition23-OSCAL/refs/heads/main/BS_GK_OSCAL_JSON_DATA/BSI_GS_OSCAL_current_2023.json"
GPP_KOMPENDIUM_JSON_PATH = "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/refs/heads/main/Anwenderkataloge/Grundschutz%2B%2B/Grundschutz%2B%2B-catalog.json"

# --- Filtering ---
ALLOWED_MAIN_GROUPS = ["SYS", "INF", "IND", "APP", "NET"]
ALLOWED_PROCESS_BAUSTEINE = ["OPS.2.2", "OPS.2.3", "OPS.3.2"]

# --- Output File Paths ---
# Output roots default to the repository's sibling-directory layout under OUTPUT_ROOT
# (== REPO_ROOT unless overridden), but each can be pointed elsewhere via an env var so
# the tool is portable to other deployment contexts (issue 3.5).
SDT_HELPER_OUTPUT_DIR = os.path.abspath(
    os.environ.get("SDT_HELPER_OUTPUT_DIR", os.path.join(OUTPUT_ROOT, "hilfsdateien"))
)
BAUSTEIN_ZIELOBJEKT_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "baustein_zielobjekt.json")
ZIELOBJEKT_CONTROLS_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "zielobjekt_controls.json")
BAUSTEIN_ZIELOBJEKTKATEGORIE_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "baustein_zielobjektkategorien.json")
ZIELOBJEKTKATEGORIE_CONTROLS_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "zielobjektkategorien_controls.json")
PROZZESSBAUSTEINE_CONTROLS_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "prozessbausteine_mapping.json")
# Per-G++-control mapping to matching BSI Edition-2023 Anforderungen (stage_ed23_anforderungen).
# Consumed by the One-Page-Apps to show the "Zeige BSI ED23 Anforderungen" panel.
GPP_ED23_ANFORDERUNGEN_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "gpp_ed23_anforderungen.json")
# A compact projection of the ED23 catalog (id | name | prose) used as the cached grounding corpus.
ED23_ANFORDERUNGEN_STRIPPED_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "ed23_anforderungen_stripped.json")
SDT_PROFILES_REGULAR_DIR = os.path.abspath(
    os.environ.get("SDT_PROFILES_REGULAR_DIR", os.path.join(OUTPUT_ROOT, "Zielobjektkategorien/profile/regular"))
)
SDT_PROFILES_PROCESS_DIR = os.path.abspath(
    os.environ.get("SDT_PROFILES_PROCESS_DIR", os.path.join(OUTPUT_ROOT, "Zielobjektkategorien/profile/process"))
)
ED23_PROFILES_DIR = os.path.abspath(
    os.environ.get("ED23_PROFILES_DIR", os.path.join(OUTPUT_ROOT, "ED23-Baustein-profile/DE"))
)



# --- Asset Paths ---
PROMPT_CONFIG_PATH = os.path.join(SRC_ROOT, "assets/json/prompt_config.json")
BAUSTEIN_TO_ZIELOBJEKT_SCHEMA_PATH = os.path.join(SRC_ROOT, "assets/schemas/baustein_to_zielobjekt_schema.json")
ENHANCED_CONTROL_RESPONSE_SCHEMA_PATH = os.path.join(SRC_ROOT, "assets/schemas/enhanced_control_response_schema.json")
ED23_ANFORDERUNGEN_RESPONSE_SCHEMA_PATH = os.path.join(SRC_ROOT, "assets/schemas/ed23_anforderungen_response_schema.json")

# --- AI Model Configuration ---
# These default to current Gemini preview identifiers. They are env-overridable so a stable,
# versioned Vertex AI model id can be pinned for reproducibility without a code change
# (issue 4.1).
GROUND_TRUTH_MODEL = os.environ.get("GROUND_TRUTH_MODEL", "gemini-3-flash-preview")
GROUND_TRUTH_MODEL_PRO = os.environ.get("GROUND_TRUTH_MODEL_PRO", "gemini-3.1-pro-preview")

# --- API Configuration ---
# Constants for external API interactions, such as retry logic parameters.
API_MAX_RETRIES = 5
API_RETRY_BACKOFF_FACTOR = 2
API_RETRY_JITTER = 0.5  # 50% jitter
API_TEMPERATURE = 1
API_MAX_OUTPUT_TOKEN = 65536

# --- Logging ---
LOG_LEVEL_TEST = "DEBUG"
LOG_LEVEL_PRODUCTION = "INFO"
THIRD_PARTY_LOG_LEVEL_PRODUCTION = "WARNING"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# --- OSCAL Metadata ---
# Default values and namespaces for OSCAL artifact generation.
OSCAL_VERSION = "1.1.3"
OSCAL_NAMESPACE = "http://csrc.nist.gov/ns/oscal/1.0"

# --- Praktiken (Practices) ---
# Maps a practice abbreviation (Kürzel, e.g. "ARCH") to its full German term (Begriff,
# e.g. "Architektur"). The process-Zielobjekt ids are these Kürzel suffixed with
# "_prozesse" (e.g. "ARCH_prozesse"), so resolving them yields readable profile titles.
# Source of truth (keep in sync):
# https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek/blob/main/Dokumentation/namespaces/practices.csv
PRACTICE_ABBREVIATIONS = {
    "GC": "Governance und Compliance",
    "STM": "Strukturmodellierung",
    "UMS": "Umsetzung",
    "VRB": "Verbesserung",
    "PERF": "Monitoring-Evaluation",
    "RISK": "Risikomanagement",
    "ASST": "Informationen und Assets",
    "PERS": "Personal",
    "BES": "Beschaffungsmanagement",
    "DLS": "Dienstleistersteuerung",
    "TEST": "Änderungen und Tests",
    "GEB": "Gebäudemanagement",
    "SENS": "Sensibilisierung",
    "ARCH": "Architektur",
    "BER": "Berechtigung",
    "NOT": "Notfallplanung",
    "DET": "Detektion",
    "REA": "Sicherheitsvorfallsbehandlung",
    "KONF": "Konfiguration",
    "DEV": "Entwicklung",
    # Not a practice per se, but used as a process-Zielobjekt id for the methodology pool.
    "METHODIK": "Methodik",
}
