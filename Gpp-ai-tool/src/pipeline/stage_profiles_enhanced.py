"""
Pipeline Stage: Enhanced Profile Generation

This stage enriches existing OSCAL profiles with AI-generated maturity sub-statements.
It relies on the data generated in earlier stages and uses AI to map BSI requirements
to the 5 maturity levels of Grundschutz++ controls.
"""

import os
import json
import uuid
import logging
import asyncio
from datetime import datetime, timezone
import urllib.parse
import sys

from config import app_config
from constants import (
    BAUSTEIN_ZIELOBJEKT_JSON_PATH,
    CONTROLS_ANFORDERUNGEN_JSON_PATH,
    BSI_2023_JSON_PATH,
    GPP_KOMPENDIUM_JSON_PATH,
    ZIELOBJEKTE_CSV_PATH,
    PROZZESSBAUSTEINE_CONTROLS_JSON_PATH,
    SDT_PROFILES_REGULAR_DIR,
    SDT_PROFILES_PROCESS_DIR,
    ED23_PROFILES_DIR,
    OSCAL_VERSION,
    ZIELOBJEKT_CONTROLS_JSON_PATH
)
from utils.file_utils import create_dir_if_not_exists, read_json_file, write_json_file, read_csv_file
from utils.text_utils import sanitize_filename
from utils.oscal_utils import (
    extract_all_gpp_controls,
    get_component_type,
    normalize_id,
    validate_oscal
)
from clients.ai_client import AiClient

logger = logging.getLogger(__name__)

# Constants for retry logic
MAX_RETRIES = 3
RETRY_DELAY = 5

def build_oscal_maturity_statements(control_id: str, title: str, generated_data: dict, original_description: str, baustein_id: str) -> list:
    """Constructs the OSCAL maturity sub-statements (parts) for the 'adds' block."""
    parts = []
    levels = [("Partial", "partial", "1"), ("Foundational", "foundational", "2"), ("Defined", "defined", "3"), ("Enhanced", "enhanced", "4"), ("Comprehensive", "comprehensive", "5")]

    props_ns = "https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek/tree/main/Dokumentation/namespaces"

    # Properties shared across all levels for this control
    base_props = [
        {"name": "control_class", "value": generated_data.get("class") or "Technical", "ns": props_ns},
        {"name": "phase", "value": generated_data.get('phase') or 'N/A', "ns": props_ns},
        {"name": "effective_on_c", "value": str(generated_data.get("effective_on_c") or "").lower(), "ns": props_ns},
        {"name": "effective_on_i", "value": str(generated_data.get("effective_on_i") or "").lower(), "ns": props_ns},
        {"name": "effective_on_a", "value": str(generated_data.get("effective_on_a") or "").lower(), "ns": props_ns},
        {"name": "level", "value": generated_data.get("level") or "N/A", "ns": props_ns},
        {"name": "practice", "value": generated_data.get("practice") or "N/A", "ns": props_ns},
    ]

    prefix = f"(BSI Baustein {baustein_id})"
    enriched_prose = f"{prefix} {original_description}".strip()

    for title_suffix, class_suffix, level_num in levels:
        statement_key = f"level_{level_num}_statement"
        guidance_key = f"level_{level_num}_guidance"
        assessment_key = f"level_{level_num}_assessment"

        statement_text = generated_data.get(statement_key)

        if statement_text:
            statement_props = list(base_props) + [
                {"name": "label", "value": f"m{level_num}"},
                {"name": "statement", "value": statement_text},
                {"name": "guidance", "value": generated_data.get(guidance_key, "")},
                {"name": "assessment-method", "value": generated_data.get(assessment_key, "")}
            ]

            parts.append({
                "id": f"{control_id}-m{level_num}_custom",
                "name": "statement",
                "props": statement_props,
                "prose": enriched_prose
            })

    return parts

async def generate_enhanced_profile_data(baustein_id: str, baustein_title: str, zielobjekt_name: str, input_profile_path: str, bsi_catalog: dict, gpp_controls_lookup: dict, ai_client: AiClient) -> dict:
    """Generates the enhanced profile alters blocks using AI."""

    if not os.path.exists(input_profile_path):
        logger.warning(f"Input profile not found for {baustein_id} at {input_profile_path}. Skipping.")
        return None

    profile = read_json_file(input_profile_path)
    if not profile:
        logger.error(f"Failed to load profile for {baustein_id} from {input_profile_path}")
        return None

    # 1. Identify Target Controls
    gpp_controls_in_profile = profile.get("profile", {}).get("imports", [{}])[0].get("include-controls", [{}])[0].get("with-ids", [])

    if not gpp_controls_in_profile:
        logger.warning(f"No G++ controls found in profile {input_profile_path}")
        return None

    # 2. Extract specific mappings and BSI requirements for context
    controls_anforderungen = read_json_file(CONTROLS_ANFORDERUNGEN_JSON_PATH)
    zielobjekt_uuid = None

    for uuid_key, data in controls_anforderungen.items():
        if data.get('baustein_id') == baustein_id:
            zielobjekt_uuid = uuid_key
            break

    mapping = controls_anforderungen.get(zielobjekt_uuid, {}).get("mapping", {}) if zielobjekt_uuid else {}

    # 3. Retrieve texts for context
    control_descriptions = {}
    for gpp_control_id in gpp_controls_in_profile:
        bsi_req_ids = mapping.get(gpp_control_id, [])
        description_parts = []
        for req_id in bsi_req_ids:
            for group in bsi_catalog.get("catalog", {}).get("groups", []):
                for baustein in group.get("groups", []):
                    if baustein.get("id") == baustein_id:
                        for req in baustein.get("controls", []):
                            if req.get("id") == req_id:
                                # Extract parts if they exist
                                for part in req.get("parts", []):
                                    if part.get("name") == "statement" or part.get("name") == "objective":
                                        description_parts.append(f"{req_id}: {part.get('prose', '')}")
        control_descriptions[gpp_control_id] = "\n".join(description_parts)

    # 4. Prompt AI
    logger.info(f"Generating AI enhancements for {len(gpp_controls_in_profile)} controls in Baustein {baustein_id}")

    # Chunking controls to avoid overwhelming the model
    CHUNK_SIZE = 10
    chunks = [gpp_controls_in_profile[i:i + CHUNK_SIZE] for i in range(0, len(gpp_controls_in_profile), CHUNK_SIZE)]

    async def process_chunk(chunk):
        context_data = []
        for ctrl_id in chunk:
            gpp_data = gpp_controls_lookup.get(ctrl_id, {})
            bsi_reqs = mapping.get(ctrl_id, [])
            bsi_texts = control_descriptions.get(ctrl_id, "")

            context_data.append({
                "gpp_control_id": ctrl_id,
                "gpp_control_title": gpp_data.get("title", ""),
                "gpp_control_prose": gpp_data.get("prose", ""),
                "mapped_bsi_requirements": bsi_reqs,
                "bsi_requirements_text": bsi_texts
            })

        for attempt in range(MAX_RETRIES):
            try:
                result = await ai_client.generate_maturity_levels_async(context_data, baustein_id)
                return result
            except Exception as e:
                logger.warning(f"AI Generation attempt {attempt+1} failed for chunk in Baustein {baustein_id}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (2 ** attempt)) # Exponential backoff
                else:
                    logger.error(f"AI Generation failed after {MAX_RETRIES} attempts for chunk in Baustein {baustein_id}")
                    return []

    chunk_tasks = [process_chunk(chunk) for chunk in chunks]

    try:
        chunk_results = await asyncio.gather(*chunk_tasks)
    except Exception as e:
        logger.error(f"AI Generation failed for one or more chunks of Baustein {baustein_id}: {e}")
        return None

    # Flatten results
    ai_response = []
    for res in chunk_results:
        if isinstance(res, list):
            ai_response.extend(res)
        elif res:
             logger.warning(f"Unexpected response type from chunk: {type(res)}")

    # Create a map for faster lookup of AI results with ID normalization
    ai_results_map = {}
    for item in ai_response:
        if 'id' in item:
            clean_id = normalize_id(item['id'])
            ai_results_map[clean_id] = item

    # 5. Build Alters Array
    alters = []

    for gpp_control_id in gpp_controls_in_profile:
        lookup_id = normalize_id(gpp_control_id)
        generated_data = ai_results_map.get(lookup_id)

        if generated_data:
            control_title = gpp_controls_lookup.get(gpp_control_id, {}).get("title", "")
            original_description = control_descriptions.get(gpp_control_id, "")

            parts = build_oscal_maturity_statements(gpp_control_id, control_title, generated_data, original_description, baustein_id)

            if parts:
                alters.append({
                    "control-id": gpp_control_id,
                    "adds": [
                        {
                            "position": "ending",
                            "by-id": f"{gpp_control_id}_stm",
                            "parts": parts
                        }
                    ]
                })
        else:
            logger.warning(f"No AI generated data for control {gpp_control_id} (Looked for '{lookup_id}' in AI response)")

    return alters


async def generate_enhanced_profile(baustein_id: str, baustein_title: str, zielobjekt_name: str, input_profile_path: str, output_path: str, bsi_catalog: dict, gpp_controls_lookup: dict, ai_client: AiClient):
    """Orchestrates the generation and saving of an enhanced profile."""
    if os.path.exists(output_path) and not app_config.overwrite_temp_files:
        logger.info(f"Enhanced profile already exists at {output_path} and OVERWRITE_TEMP_FILES is false. Skipping.")
        return

    alters = await generate_enhanced_profile_data(baustein_id, baustein_title, zielobjekt_name, input_profile_path, bsi_catalog, gpp_controls_lookup, ai_client)

    if alters:
        profile = read_json_file(input_profile_path)

        # Add modify -> alters to the existing profile
        profile["profile"]["modify"] = {
            "alters": alters
        }

        # Update metadata
        profile["profile"]["metadata"]["title"] += " - Enhanced"
        profile["profile"]["metadata"]["last-modified"] = datetime.now(timezone.utc).isoformat()

        write_json_file(output_path, profile)
        # Note: Validating against profile schema if available, otherwise just basic JSON check
        logger.info(f"Successfully generated enhanced profile at {output_path}")
    else:
        logger.warning(f"Failed to generate alters data for {baustein_id}. No enhanced profile created.")


async def run_stage_profiles_enhanced():
    """Executes the enhanced profile generation stage."""
    logger.info("Starting Stage: Enhanced Profile Generation")

    # Initialize AI Client
    try:
        ai_client = AiClient(app_config)
    except Exception as e:
        logger.critical(f"Failed to initialize AI Client: {e}", exc_info=True)
        sys.exit(1)

    try:
        # Base (input) profiles are read from the SDT_PROFILES_* dirs produced by
        # the earlier profile stage; the enhanced (output) profiles generated from
        # the BSI 2023 edition are written to ED23_PROFILES_DIR.
        create_dir_if_not_exists(SDT_PROFILES_REGULAR_DIR)
        create_dir_if_not_exists(SDT_PROFILES_PROCESS_DIR)
        create_dir_if_not_exists(ED23_PROFILES_DIR)
    except OSError as e:
        logger.critical(f"Failed to create output directories: {e}", exc_info=True)
        raise

    try:
        zielobjekte_data = read_csv_file(ZIELOBJEKTE_CSV_PATH)
        if not zielobjekte_data:
            raise FileNotFoundError(f"Zielobjekte data is empty or could not be loaded from {ZIELOBJEKTE_CSV_PATH}")
        zielobjekt_name_map = {row['UUID'].strip(): row['Zielobjekt'].strip() for row in zielobjekte_data if 'UUID' in row and 'Zielobjekt' in row}
    except (IOError, FileNotFoundError, TypeError, KeyError) as e:
        logger.critical(f"Failed to load or parse Zielobjekte CSV data: {e}", exc_info=True)
        raise

    try:
        baustein_zielobjekt_map = read_json_file(BAUSTEIN_ZIELOBJEKT_JSON_PATH)
        controls_anforderungen = read_json_file(CONTROLS_ANFORDERUNGEN_JSON_PATH)
        prozessbausteine_mapping = read_json_file(PROZZESSBAUSTEINE_CONTROLS_JSON_PATH)
        bsi_catalog = read_json_file(BSI_2023_JSON_PATH)
        gpp_catalog = read_json_file(GPP_KOMPENDIUM_JSON_PATH)
        zielobjekt_controls = read_json_file(ZIELOBJEKT_CONTROLS_JSON_PATH)

        # Check each loaded data file individually
        data_to_check = {
            BAUSTEIN_ZIELOBJEKT_JSON_PATH: baustein_zielobjekt_map,
            CONTROLS_ANFORDERUNGEN_JSON_PATH: controls_anforderungen,
            PROZZESSBAUSTEINE_CONTROLS_JSON_PATH: prozessbausteine_mapping,
            BSI_2023_JSON_PATH: bsi_catalog,
            GPP_KOMPENDIUM_JSON_PATH: gpp_catalog,
            ZIELOBJEKT_CONTROLS_JSON_PATH: zielobjekt_controls
        }
        for path, data in data_to_check.items():
            if not data:
                raise IOError(f"Data file loaded from '{path}' is empty or could not be loaded.")
    except (IOError, FileNotFoundError, Exception) as e:
        logger.critical(f"Failed to load critical data for enhanced profile generation: {e}", exc_info=True)
        sys.exit(1)

    baustein_titles = {
        value['baustein_id']: value['zielobjekt_name']
        for value in controls_anforderungen.values() if 'baustein_id' in value and 'zielobjekt_name' in value
    }

    bsi_baustein_title_lookup = {}
    for group in bsi_catalog.get("catalog", {}).get("groups", []):
        for baustein in group.get("groups", []):
            if baustein.get("id") and baustein.get("title"):
                bsi_baustein_title_lookup[baustein["id"]] = baustein["title"]

    logger.info("Extracting G++ controls for lookup...")
    gpp_controls_lookup = extract_all_gpp_controls(gpp_catalog)
    logger.info(f"Successfully extracted {len(gpp_controls_lookup)} G++ controls.")

    sem = asyncio.Semaphore(app_config.max_concurrent_ai_requests)

    async def process_single_baustein(baustein_id, zielobjekt_uuid):
        async with sem:
            logger.info(f"Processing Baustein: {baustein_id}")

            zielobjekt_name = zielobjekt_name_map.get(zielobjekt_uuid)

            is_process = False
            if zielobjekt_uuid == "Methodik" or str(zielobjekt_uuid).endswith("_prozesse"):
                zielobjekt_name = zielobjekt_uuid
                is_process = True

            if not zielobjekt_name:
                logger.warning(f"No name found for Zielobjekt UUID {zielobjekt_uuid} (Baustein {baustein_id}). Skipping.")
                return

            baustein_title = baustein_titles.get(baustein_id) or bsi_baustein_title_lookup.get(baustein_id)
            if not baustein_title:
                logger.warning(f"No title found for Baustein ID {baustein_id}. Using Zielobjekt name as fallback.")
                baustein_title = zielobjekt_name

            sanitized_name = sanitize_filename(zielobjekt_name)

            if is_process:
                input_filename = f"{sanitized_name}_process_profile.json"
                input_path = os.path.join(SDT_PROFILES_PROCESS_DIR, input_filename)
                output_filename = f"{sanitized_name}_process_profile_enhanced.json"
            else:
                input_filename = f"{sanitized_name}_profile.json"
                input_path = os.path.join(SDT_PROFILES_REGULAR_DIR, input_filename)
                output_filename = f"{sanitized_name}_profile_enhanced.json"

            output_path = os.path.join(ED23_PROFILES_DIR, output_filename)

            await generate_enhanced_profile(baustein_id, baustein_title, zielobjekt_name, input_path, output_path, bsi_catalog, gpp_controls_lookup, ai_client)

    tasks = []

    # Run through the regular mappings
    for baustein_id, zielobjekt_uuid in baustein_zielobjekt_map.get("baustein_zielobjekt_map", {}).items():
        tasks.append(process_single_baustein(baustein_id, zielobjekt_uuid))

    # Also process standard Zielobjekte that might not be directly in the map
    processed_uuids = set(baustein_zielobjekt_map.get("baustein_zielobjekt_map", {}).values())

    for zielobjekt_uuid, controls in zielobjekt_controls.get("zielobjekt_controls_map", {}).items():
        if zielobjekt_uuid not in processed_uuids:
            # For these, the baustein_id is roughly equivalent to the zielobjekt_uuid context
            if zielobjekt_uuid == "Methodik" or zielobjekt_uuid.endswith("_prozesse"):
                tasks.append(process_single_baustein(zielobjekt_uuid, zielobjekt_uuid))

    await asyncio.gather(*tasks)

    logger.info("Finished Stage: Enhanced Profile Generation")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(run_stage_profiles_enhanced())
