"""
Pipeline Stage: Profile Generation

This stage generates OSCAL (Open Security Controls Assessment Language) profiles for
each Zielobjekt based on the controls mapped in the ZIELOBJEKT_CONTROLS_JSON_PATH file.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone

from config import app_config
from constants import (
    ZIELOBJEKT_CONTROLS_JSON_PATH,
    SDT_PROFILES_REGULAR_DIR,
    SDT_PROFILES_PROCESS_DIR,
    ZIELOBJEKTKATEGORIEN_CSV_PATH,
    OSCAL_VERSION,
    PRACTICE_ABBREVIATIONS,
)
from utils.file_utils import create_dir_if_not_exists, read_json_file, write_json_file, read_csv_file
from utils.text_utils import sanitize_filename

# Configure logging
logger = logging.getLogger(__name__)

# Stable namespace for deriving deterministic (UUIDv5) profile UUIDs, so re-running the
# pipeline yields identical UUIDs for the same Zielobjekt/Prozess and the generated
# profiles don't churn in git.
PROFILE_UUID_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL,
    "https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek/base-profiles",
)


def resolve_practice_name(practice_key):
    """Resolves a practice abbreviation (e.g. "arch") to its full term ("Architektur").

    Falls back to the original key if it is not a known abbreviation.
    """
    return PRACTICE_ABBREVIATIONS.get((practice_key or "").upper(), practice_key)


def create_oscal_profile(profile_uuid, title, controls):
    """
    Creates a basic OSCAL profile for a given Zielobjekt.

    Args:
        profile_uuid (str): The (deterministic) UUID for the profile.
        title (str): The human-readable profile title.
        controls (list): A list of control IDs to include in the profile.

    Returns:
        dict: The OSCAL profile as a dictionary.
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    catalog_url = "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/refs/heads/main/Anwenderkataloge/Grundschutz%2B%2B/Grundschutz%2B%2B-catalog.json"

    profile = {
        "profile": {
            "uuid": profile_uuid,
            "metadata": {
                "title": title,
                "last-modified": now_utc,
                "version": "0.0.1",
                "oscal-version": OSCAL_VERSION
            },
            "imports": [
                {
                    "href": catalog_url,
                    "include-controls": [
                        {
                            "with-ids": controls
                        }
                    ]
                }
            ]
        }
    }
    return profile

def run_stage_profiles():
    """
    Executes the profile generation stage.
    """
    logger.info("Starting Stage: Profile Generation")

    create_dir_if_not_exists(SDT_PROFILES_REGULAR_DIR)
    create_dir_if_not_exists(SDT_PROFILES_PROCESS_DIR)

    zielobjekt_controls = read_json_file(ZIELOBJEKT_CONTROLS_JSON_PATH)
    if not zielobjekt_controls:
        logger.error(f"Could not load Zielobjekt controls from {ZIELOBJEKT_CONTROLS_JSON_PATH}")
        return

    zielobjekte_data = read_csv_file(ZIELOBJEKTKATEGORIEN_CSV_PATH)
    if not zielobjekte_data:
        logger.error(f"Could not load Zielobjekte from {ZIELOBJEKTKATEGORIEN_CSV_PATH}")
        return

    zielobjekt_name_map = {row['UUID']: row['Zielobjektkategorie'] for row in zielobjekte_data if 'UUID' in row and 'Zielobjektkategorie' in row}

    for zielobjekt_id, controls in zielobjekt_controls.get("zielobjekt_controls_map", {}).items():
        zielobjekt_name = ""
        is_process = False

        if zielobjekt_id == "Methodik" or zielobjekt_id.endswith("_prozesse"):
            zielobjekt_name = zielobjekt_id
            is_process = True
        elif zielobjekt_id in zielobjekt_name_map:
            zielobjekt_name = zielobjekt_name_map[zielobjekt_id]
            # Some process bausteine could still land here, but generally they're caught by the name check above
            # Or if they are normal profiles, is_process = False
        else:
            logger.warning(f"No name found for Zielobjekt with UUID {zielobjekt_id}. Skipping profile generation.")
            continue

        sanitized_name = sanitize_filename(zielobjekt_name)

        if is_process:
            display_name = sanitized_name
            if display_name.endswith("_prozesse"):
                display_name = display_name[:-9]
            # e.g. "ARCH_prozesse" -> "Architektur Prozess Profil"
            title = f"{resolve_practice_name(display_name)} Prozess Profil"
            profile_uuid = str(uuid.uuid5(PROFILE_UUID_NAMESPACE, f"process|{display_name.upper()}"))
            output_filename = f"{display_name}_process_profile.json"
            output_path = os.path.join(SDT_PROFILES_PROCESS_DIR, output_filename)
        else:
            # e.g. "Administrierende" -> "Administrierende Zielobjektkategorie Profil"
            title = f"{zielobjekt_name} Zielobjektkategorie Profil"
            profile_uuid = str(uuid.uuid5(PROFILE_UUID_NAMESPACE, f"regular|{zielobjekt_id}"))
            output_filename = f"{sanitized_name}_profile.json"
            output_path = os.path.join(SDT_PROFILES_REGULAR_DIR, output_filename)

        profile = create_oscal_profile(profile_uuid, title, controls)

        if os.path.exists(output_path) and not app_config.overwrite_temp_files:
            logger.info(f"Profile already exists at {output_path} and OVERWRITE_TEMP_FILES is false. Skipping.")
            continue

        write_json_file(output_path, profile)
        logger.info(f"Generated OSCAL profile for {zielobjekt_name} at {output_path}")

    logger.info("Finished Stage: Profile Generation")

if __name__ == '__main__':
    # This allows the script to be run directly for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    run_stage_profiles()
