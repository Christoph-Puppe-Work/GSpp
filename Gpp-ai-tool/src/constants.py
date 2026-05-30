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
# REPO_ROOT is the parent directory of the 'Gpp-ai-tool' project folder.
REPO_ROOT = os.path.abspath(os.path.join(SRC_ROOT, "..", ".."))

# ANFORDERUNG_ID_PATTERN = re.compile(r"^[A-Z]{2,}(\.\d+)+(?:.A\d+)?$")
ANFORDERUNG_ID_PATTERN = re.compile(r"^.*$")

# --- Data Source URLs ---
# Input data is fetched directly from the upstream GitHub repositories (raw
# content) rather than from local submodule checkouts. The loaders in
# utils/data_loader.py and utils/file_utils.py transparently download these.
ZIELOBJEKTE_CSV_PATH = "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/refs/heads/main/Dokumentation/namespaces/target_object_categories.csv"
BSI_2023_JSON_PATH = "https://raw.githubusercontent.com/NTTDATA-DACH/BSI-GS-Benutzerdefinierte-Edition23-OSCAL/refs/heads/main/BS_GK_OSCAL_JSON_DATA/BSI_GS_OSCAL_current_2023_benutzerdefinierte.json"
GPP_KOMPENDIUM_JSON_PATH = "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/refs/heads/main/Anwenderkataloge/Grundschutz%2B%2B/Grundschutz%2B%2B-catalog.json"

# --- Filtering ---
ALLOWED_MAIN_GROUPS = ["SYS", "INF", "IND", "APP", "NET"]
ALLOWED_PROCESS_BAUSTEINE = ["OPS.2.2", "OPS.2.3", "OPS.3.2"]

# --- Output to Stand der Technik Submodule File Paths ---
SDT_HELPER_OUTPUT_DIR = os.path.join(REPO_ROOT, "hilfsdateien")
BAUSTEIN_ZIELOBJEKT_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "baustein_zielobjekt.json")
CONTROLS_ANFORDERUNGEN_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "controls_anforderungen.json")
ZIELOBJEKT_CONTROLS_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "zielobjekt_controls.json")
PROZZESSBAUSTEINE_CONTROLS_JSON_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "prozessbausteine_mapping.json")
SDT_PROFILES_REGULAR_DIR = os.path.join(REPO_ROOT, "Zielobjektkategorien/profile/regular")
SDT_PROFILES_PROCESS_DIR = os.path.join(REPO_ROOT, "Zielobjektkategorien/profile/process")
ED23_PROFILES_DIR = os.path.join(REPO_ROOT, "ED23-Baustein-profile/")



# Paths for the 'stage_strip' output files

GPP_STRIPPED_MD_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "gpp_stripped.md")
GPP_STRIPPED_ISMS_MD_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "gpp_isms_stripped.md")
BSI_STRIPPED_MD_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "bsi_2023_stripped.md")
BSI_STRIPPED_ISMS_MD_PATH = os.path.join(SDT_HELPER_OUTPUT_DIR, "bsi_2023_stripped_ISMS.md")


# --- Asset Paths ---
PROMPT_CONFIG_PATH = os.path.join(SRC_ROOT, "assets/json/prompt_config.json")
BAUSTEIN_TO_ZIELOBJEKT_SCHEMA_PATH = os.path.join(SRC_ROOT, "assets/schemas/baustein_to_zielobjekt_schema.json")
ANFORDERUNG_TO_KONTROLLE_SCHEMA_PATH = os.path.join(SRC_ROOT, "assets/schemas/anforderung_to_kontrolle_schema.json")
MATCHING_SCHEMA_PATH = os.path.join(SRC_ROOT, "assets/schemas/matching_schema.json")
OSCAL_COMPONENT_SCHEMA_PATH = os.path.join(REPO_ROOT, "oscal_json_schemas/oscal_component_schema.json")

# --- AI Model Configuration ---
GROUND_TRUTH_MODEL = "gemini-3-flash-preview"
GROUND_TRUTH_MODEL_PRO = "gemini-3.1-pro-preview"

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
