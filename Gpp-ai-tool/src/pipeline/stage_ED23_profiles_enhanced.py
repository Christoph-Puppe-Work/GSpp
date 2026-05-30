"""
Pipeline Stage: ED2023 Enhanced Profile Generation

This stage takes the per-Zielobjekt base OSCAL profiles produced by `stage_profiles`
(which import the G++ catalog and include *all* controls of the Zielobjektkategorie) and
enriches every control with AI-generated maturity sub-statements (levels 1-5) plus
classifications (NIST class, ISMS phase, CIA), emitted as OSCAL `alter` blocks.

The enrichment is driven by best practices (the prompt) and the description of the BSI
Baustein the profile is based on — it does NOT depend on any per-Anforderung mapping.
One enhanced profile is written per Baustein to ED23_PROFILES_DIR.
"""

import os
import logging
import asyncio
from datetime import datetime, timezone
import sys

from config import app_config
from constants import (
    BAUSTEIN_ZIELOBJEKT_JSON_PATH,
    BSI_2023_JSON_PATH,
    GPP_KOMPENDIUM_JSON_PATH,
    ZIELOBJEKTE_CSV_PATH,
    SDT_PROFILES_REGULAR_DIR,
    SDT_PROFILES_PROCESS_DIR,
    ED23_PROFILES_DIR,
    ZIELOBJEKT_CONTROLS_JSON_PATH,
    PROMPT_CONFIG_PATH,
    ENHANCED_CONTROL_RESPONSE_SCHEMA_PATH,
)
from utils.file_utils import create_dir_if_not_exists, read_json_file, write_json_file, read_csv_file
from utils.text_utils import sanitize_filename
from utils.data_parser import find_bausteine_with_prose
from utils.oscal_utils import extract_all_gpp_controls, normalize_id
from clients.ai_client import AiClient

logger = logging.getLogger(__name__)

# Chunk controls to avoid overwhelming the model in a single request.
CHUNK_SIZE = 10


def build_oscal_maturity_statements(control_id: str, generated_data: dict, original_description: str, baustein_id: str) -> list:
    """Constructs the OSCAL maturity sub-statements (parts) for the 'adds' block."""
    parts = []
    levels = ["1", "2", "3", "4", "5"]

    props_ns = "https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek/tree/main/Dokumentation/namespaces"

    # Properties shared across all levels for this control
    base_props = [
        {"name": "control_class", "value": generated_data.get("class") or "Technical", "ns": props_ns},
        {"name": "phase", "value": generated_data.get('phase') or 'N/A', "ns": props_ns},
        {"name": "effective_on_c", "value": str(generated_data.get("effective_on_c") or "").lower(), "ns": props_ns},
        {"name": "effective_on_i", "value": str(generated_data.get("effective_on_i") or "").lower(), "ns": props_ns},
        {"name": "effective_on_a", "value": str(generated_data.get("effective_on_a") or "").lower(), "ns": props_ns},
    ]

    prefix = f"(BSI Baustein {baustein_id})"
    enriched_prose = f"{prefix} {original_description}".strip()

    for level_num in levels:
        statement_text = generated_data.get(f"level_{level_num}_statement")

        if statement_text:
            statement_props = list(base_props) + [
                {"name": "label", "value": f"m{level_num}"},
                {"name": "statement", "value": statement_text},
                {"name": "guidance", "value": generated_data.get(f"level_{level_num}_guidance", "")},
                {"name": "assessment-method", "value": generated_data.get(f"level_{level_num}_assessment", "")}
            ]

            parts.append({
                "id": f"{control_id}-m{level_num}_custom",
                "name": "statement",
                "props": statement_props,
                "prose": enriched_prose
            })

    return parts


def _render_controls_table(control_ids: list, gpp_controls_lookup: dict) -> str:
    """Renders a markdown table of the G++ controls to enrich (ID, title, prose)."""
    header = "| ID | Title | Prose |\n|---|---|---|\n"
    rows = []
    for ctrl_id in control_ids:
        data = gpp_controls_lookup.get(ctrl_id, {})
        title = (data.get("title", "") or "").replace("\n", " ")
        prose = (data.get("prose", "") or "").replace("\n", " ")
        rows.append(f"| {ctrl_id} | {title} | {prose} |")
    return header + "\n".join(rows)


async def generate_enhanced_profile_data(
    baustein_id: str,
    baustein_title: str,
    baustein_description: str,
    input_profile_path: str,
    gpp_controls_lookup: dict,
    prompt_instruction: str,
    enhanced_schema: dict,
    ai_client: AiClient,
) -> list:
    """Generates the enhanced profile 'alters' blocks using AI for all controls in the profile."""

    if not os.path.exists(input_profile_path):
        logger.warning(f"Input profile not found for {baustein_id} at {input_profile_path}. Skipping.")
        return None

    profile = read_json_file(input_profile_path)
    if not profile:
        logger.error(f"Failed to load profile for {baustein_id} from {input_profile_path}")
        return None

    # All controls of the Zielobjektkategorie are already included in the base profile.
    gpp_controls_in_profile = profile.get("profile", {}).get("imports", [{}])[0].get("include-controls", [{}])[0].get("with-ids", [])

    if not gpp_controls_in_profile:
        logger.warning(f"No G++ controls found in profile {input_profile_path}")
        return None

    logger.info(f"Generating AI enhancements for {len(gpp_controls_in_profile)} controls in Baustein {baustein_id}")

    baustein_context = (
        f"**Context — the BSI IT-Grundschutz Baustein this profile is based on:**\n"
        f"* ID: {baustein_id}\n"
        f"* Title: {baustein_title}\n"
        f"* Description: {baustein_description or 'N/A'}\n\n"
    )

    chunks = [gpp_controls_in_profile[i:i + CHUNK_SIZE] for i in range(0, len(gpp_controls_in_profile), CHUNK_SIZE)]

    async def process_chunk(chunk):
        prompt = (
            f"{prompt_instruction}\n\n"
            f"{baustein_context}"
            f"**G++ controls to enrich** (generate maturity levels 1-5 for each; "
            f"Level 3 must be an exact copy of the control's prose):\n"
            f"{_render_controls_table(chunk, gpp_controls_lookup)}\n\n"
            "Return a JSON array with one object per control, matching each by its original ID."
        )
        try:
            result = await ai_client.generate_validated_json_response(
                prompt=prompt,
                json_schema=enhanced_schema,
                request_context_log=f"ED23Enhance-{baustein_id}",
            )
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"AI enhancement failed for a chunk of Baustein {baustein_id}: {e}")
            return []

    chunk_results = await asyncio.gather(*[process_chunk(chunk) for chunk in chunks])

    # Flatten and index AI results by normalized control ID
    ai_results_map = {}
    for res in chunk_results:
        for item in res:
            if isinstance(item, dict) and 'id' in item:
                ai_results_map[normalize_id(item['id'])] = item

    alters = []
    for gpp_control_id in gpp_controls_in_profile:
        generated_data = ai_results_map.get(normalize_id(gpp_control_id))
        if not generated_data:
            logger.warning(f"No AI generated data for control {gpp_control_id} in Baustein {baustein_id}")
            continue

        original_description = gpp_controls_lookup.get(gpp_control_id, {}).get("prose", "")
        parts = build_oscal_maturity_statements(gpp_control_id, generated_data, original_description, baustein_id)

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

    return alters


async def generate_enhanced_profile(
    baustein_id: str,
    baustein_title: str,
    baustein_description: str,
    input_profile_path: str,
    output_path: str,
    gpp_controls_lookup: dict,
    prompt_instruction: str,
    enhanced_schema: dict,
    ai_client: AiClient,
):
    """Orchestrates the generation and saving of an enhanced profile."""
    if os.path.exists(output_path) and not app_config.overwrite_temp_files:
        logger.info(f"Enhanced profile already exists at {output_path} and OVERWRITE_TEMP_FILES is false. Skipping.")
        return

    alters = await generate_enhanced_profile_data(
        baustein_id, baustein_title, baustein_description, input_profile_path,
        gpp_controls_lookup, prompt_instruction, enhanced_schema, ai_client,
    )

    if alters:
        profile = read_json_file(input_profile_path)
        profile["profile"]["modify"] = {"alters": alters}
        profile["profile"]["metadata"]["title"] += " - Enhanced (ED2023)"
        profile["profile"]["metadata"]["last-modified"] = datetime.now(timezone.utc).isoformat()

        write_json_file(output_path, profile)
        logger.info(f"Successfully generated enhanced profile at {output_path}")
    else:
        logger.warning(f"Failed to generate alters data for {baustein_id}. No enhanced profile created.")


async def run_stage_ED23_profiles_enhanced():
    """Executes the ED2023 enhanced profile generation stage."""
    logger.info("Starting Stage: ED2023 Enhanced Profile Generation")

    try:
        ai_client = AiClient(app_config)
    except Exception as e:
        logger.critical(f"Failed to initialize AI Client: {e}", exc_info=True)
        sys.exit(1)

    try:
        # Base (input) profiles come from the SDT_PROFILES_* dirs produced by
        # stage_profiles; the enhanced (output) profiles are written to ED23_PROFILES_DIR.
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
        zielobjekt_name_map = {row['UUID'].strip(): row['Zielobjektkategorie'].strip() for row in zielobjekte_data if 'UUID' in row and 'Zielobjektkategorie' in row}
    except (IOError, FileNotFoundError, TypeError, KeyError) as e:
        logger.critical(f"Failed to load or parse Zielobjekte CSV data: {e}", exc_info=True)
        raise

    try:
        baustein_zielobjekt_map = read_json_file(BAUSTEIN_ZIELOBJEKT_JSON_PATH)
        bsi_catalog = read_json_file(BSI_2023_JSON_PATH)
        gpp_catalog = read_json_file(GPP_KOMPENDIUM_JSON_PATH)
        zielobjekt_controls = read_json_file(ZIELOBJEKT_CONTROLS_JSON_PATH)
        prompt_config = read_json_file(PROMPT_CONFIG_PATH)
        enhanced_schema = read_json_file(ENHANCED_CONTROL_RESPONSE_SCHEMA_PATH)

        data_to_check = {
            BAUSTEIN_ZIELOBJEKT_JSON_PATH: baustein_zielobjekt_map,
            BSI_2023_JSON_PATH: bsi_catalog,
            GPP_KOMPENDIUM_JSON_PATH: gpp_catalog,
            ZIELOBJEKT_CONTROLS_JSON_PATH: zielobjekt_controls,
            PROMPT_CONFIG_PATH: prompt_config,
            ENHANCED_CONTROL_RESPONSE_SCHEMA_PATH: enhanced_schema,
        }
        for path, data in data_to_check.items():
            if not data:
                raise IOError(f"Data file loaded from '{path}' is empty or could not be loaded.")
    except (IOError, FileNotFoundError, Exception) as e:
        logger.critical(f"Failed to load critical data for enhanced profile generation: {e}", exc_info=True)
        sys.exit(1)

    prompt_instruction = prompt_config["generate_enhanced_controls_prompt"]

    # Baustein title (all bausteine) and usage description (ALLOWED bausteine with prose)
    bsi_baustein_title_lookup = {}
    for group in bsi_catalog.get("catalog", {}).get("groups", []):
        for baustein in group.get("groups", []):
            if baustein.get("id") and baustein.get("title"):
                bsi_baustein_title_lookup[baustein["id"]] = baustein["title"]

    baustein_desc_lookup = {b["id"]: b.get("description", "") for b in find_bausteine_with_prose(bsi_catalog)}

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

            baustein_title = bsi_baustein_title_lookup.get(baustein_id) or zielobjekt_name
            baustein_description = baustein_desc_lookup.get(baustein_id, "")

            sanitized_name = sanitize_filename(zielobjekt_name)

            if is_process:
                input_path = os.path.join(SDT_PROFILES_PROCESS_DIR, f"{sanitized_name}_process_profile.json")
            else:
                input_path = os.path.join(SDT_PROFILES_REGULAR_DIR, f"{sanitized_name}_profile.json")

            # ED23 profiles are per-Baustein, so the filename combines the
            # Zielobjektkategorie, the Baustein ID (kept readable, e.g. INF.8)
            # and the Baustein name.
            output_filename = f"{sanitized_name}_{baustein_id}_{sanitize_filename(baustein_title)}.json"
            output_path = os.path.join(ED23_PROFILES_DIR, output_filename)

            await generate_enhanced_profile(
                baustein_id, baustein_title, baustein_description, input_path, output_path,
                gpp_controls_lookup, prompt_instruction, enhanced_schema, ai_client,
            )

    tasks = []

    # Run through the Baustein -> Zielobjekt mappings from stage_match_bausteine.
    for baustein_id, zielobjekt_uuid in baustein_zielobjekt_map.get("baustein_zielobjekt_map", {}).items():
        tasks.append(process_single_baustein(baustein_id, zielobjekt_uuid))

    # Also process standard/process Zielobjekte that are not directly in the map.
    processed_uuids = set(baustein_zielobjekt_map.get("baustein_zielobjekt_map", {}).values())
    for zielobjekt_uuid in zielobjekt_controls.get("zielobjekt_controls_map", {}):
        if zielobjekt_uuid not in processed_uuids:
            if zielobjekt_uuid == "Methodik" or zielobjekt_uuid.endswith("_prozesse"):
                tasks.append(process_single_baustein(zielobjekt_uuid, zielobjekt_uuid))

    await asyncio.gather(*tasks)

    logger.info("Finished Stage: ED2023 Enhanced Profile Generation")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(run_stage_ED23_profiles_enhanced())
