"""
Pipeline Stage: Base Process Enhanced Profile Generation

This stage takes the process profiles from `SDT_PROFILES_PROCESS_DIR`
and enriches every control with AI-generated maturity sub-statements (levels 1-5)
plus classifications (NIST class, ISMS phase, CIA), emitted as OSCAL `alter` blocks.
The enhanced profile is written back to the same directory with `_enhanced.json` appended.
"""

import os
import logging
import asyncio
import uuid
from datetime import datetime, timezone
import sys

from config import app_config
from constants import (
    BAUSTEIN_ZIELOBJEKT_JSON_PATH,
    BSI_2023_JSON_PATH,
    GPP_KOMPENDIUM_JSON_PATH,
    ZIELOBJEKTKATEGORIEN_CSV_PATH,
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
from utils.oscal_utils import extract_all_gpp_controls, normalize_id, validate_enhanced_profile_structure
from clients.ai_client import AiClient

logger = logging.getLogger(__name__)

# Chunk controls to avoid overwhelming the model in a single request.
CHUNK_SIZE = 10


def build_oscal_maturity_statements(control_id: str, generated_data: dict, original_description: str, baustein_id: str) -> list:
    """Constructs the OSCAL maturity sub-statements (parts) for the 'adds' block.

    Each maturity level becomes one `statement` part whose own per-level text lives in
    `prose` (the OSCAL-idiomatic place for it), with the guidance and assessment carried as
    nested `guidance` / `assessment` parts. Classification (class, phase, CIA) and the
    level `label` stay as props — they are genuinely metadata, not prose (issue 3.1).
    """
    parts = []
    levels = ["1", "2", "3", "4", "5"]

    props_ns = "https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek/tree/main/Dokumentation/namespaces"

    # Classification properties shared across all levels for this control.
    base_props = [
        {"name": "control_class", "value": generated_data.get("class") or "Technical", "ns": props_ns},
        {"name": "phase", "value": generated_data.get('phase') or 'N/A', "ns": props_ns},
        {"name": "effective_on_c", "value": str(generated_data.get("effective_on_c") or "").lower(), "ns": props_ns},
        {"name": "effective_on_i", "value": str(generated_data.get("effective_on_i") or "").lower(), "ns": props_ns},
        {"name": "effective_on_a", "value": str(generated_data.get("effective_on_a") or "").lower(), "ns": props_ns},
    ]

    for level_num in levels:
        # Level 3 ("Defined") is the documented baseline and MUST equal the original G++
        # control prose verbatim. We inject it deterministically rather than trusting the
        # model to copy it without altering text or variable definitions (issue 2.2).
        if level_num == "3":
            statement_text = original_description or generated_data.get("level_3_statement")
        else:
            statement_text = generated_data.get(f"level_{level_num}_statement")

        if not statement_text:
            continue

        part_id = f"{control_id}-m{level_num}_custom"
        statement_props = list(base_props) + [
            {"name": "label", "value": f"m{level_num}"},
        ]

        part = {
            "id": part_id,
            "name": "statement",
            "props": statement_props,
            # The maturity-level statement itself is the prose, so a generic OSCAL
            # renderer shows the real per-level content (not a duplicated description).
            "prose": statement_text,
        }

        # Guidance and assessment become nested parts rather than custom props.
        nested = []
        guidance_text = generated_data.get(f"level_{level_num}_guidance", "")
        assessment_text = generated_data.get(f"level_{level_num}_assessment", "")
        if guidance_text:
            nested.append({
                "id": f"{part_id}_gdn",
                "name": "guidance",
                "prose": guidance_text,
            })
        if assessment_text:
            nested.append({
                "id": f"{part_id}_asm",
                "name": "assessment",
                "prose": assessment_text,
            })
        if nested:
            part["parts"] = nested

        parts.append(part)

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
            f"**G++ controls to enrich** (generate maturity levels 1, 2, 4 and 5 for each; "
            f"Level 3 is the control's prose and is injected automatically, so you may omit "
            f"level_3_* — only provide a level if a technically sound, distinct "
            f"implementation can be described):\n"
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

        control_meta = gpp_controls_lookup.get(gpp_control_id, {})
        original_description = control_meta.get("prose", "")

        # Anchor the new sub-statements to the control's real statement part. If the
        # catalog control has no statement part there is nothing to attach to, so skip
        # it rather than emit an unresolvable `by-id` (issue 3.4).
        statement_part_id = control_meta.get("statement_part_id")
        if not statement_part_id:
            logger.warning(
                f"Control {gpp_control_id} (Baustein {baustein_id}) has no statement part "
                f"to anchor maturity additions to; skipping its alter block."
            )
            continue

        parts = build_oscal_maturity_statements(gpp_control_id, generated_data, original_description, baustein_id)

        if parts:
            alters.append({
                "control-id": gpp_control_id,
                "adds": [
                    {
                        "position": "ending",
                        "by-id": statement_part_id,
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
        # The base process profile already carries a readable title (e.g. "Architektur
        # Prozess Profil") and a deterministic UUID; inherit and extend both so this
        # enhanced artifact gets its own stable UUID instead of colliding with the base.
        base_uuid = profile["profile"].get("uuid", "")
        profile["profile"]["uuid"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{base_uuid}|enhanced-ed2023"))
        profile["profile"]["metadata"]["title"] += " - Enhanced (ED2023)"
        profile["profile"]["metadata"]["last-modified"] = datetime.now(timezone.utc).isoformat()

        # Structurally validate the generated profile before writing (issue 3.3). Warn-only:
        # problems are logged but the artifact is still written.
        problems = validate_enhanced_profile_structure(profile)
        if problems:
            logger.warning(
                f"Enhanced process profile '{baustein_title}' has {len(problems)} structural "
                f"issue(s): " + "; ".join(problems[:10]) + (" ..." if len(problems) > 10 else "")
            )

        write_json_file(output_path, profile)
        logger.info(f"Successfully generated enhanced profile at {output_path}")
    else:
        logger.warning(f"Failed to generate alters data for {baustein_id}. No enhanced profile created.")


async def run_stage_base_process_enhanced():
    """Executes the Base Process enhanced profile generation stage."""
    logger.info("Starting Stage: Base Process Enhanced Profile Generation")

    try:
        ai_client = AiClient(app_config)
    except Exception as e:
        logger.critical(f"Failed to initialize AI Client: {e}", exc_info=True)
        sys.exit(1)

    try:
        create_dir_if_not_exists(SDT_PROFILES_PROCESS_DIR)
    except OSError as e:
        logger.critical(f"Failed to create output directories: {e}", exc_info=True)
        raise

    try:
        gpp_catalog = read_json_file(GPP_KOMPENDIUM_JSON_PATH)
        prompt_config = read_json_file(PROMPT_CONFIG_PATH)
        enhanced_schema = read_json_file(ENHANCED_CONTROL_RESPONSE_SCHEMA_PATH)

        data_to_check = {
            GPP_KOMPENDIUM_JSON_PATH: gpp_catalog,
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

    logger.info("Extracting G++ controls for lookup...")
    gpp_controls_lookup = extract_all_gpp_controls(gpp_catalog)
    logger.info(f"Successfully extracted {len(gpp_controls_lookup)} G++ controls.")

    sem = asyncio.Semaphore(app_config.max_concurrent_ai_requests)

    async def process_single_file(filename):
        async with sem:
            logger.info(f"Processing process profile: {filename}")

            input_path = os.path.join(SDT_PROFILES_PROCESS_DIR, filename)
            base_name = filename[:-5] # remove .json
            output_filename = f"{base_name}_enhanced.json"
            output_path = os.path.join(SDT_PROFILES_PROCESS_DIR, output_filename)

            # For process profiles, we use the base name as title and leave description empty.
            baustein_id = ""
            baustein_title = base_name
            baustein_description = ""

            await generate_enhanced_profile(
                baustein_id, baustein_title, baustein_description, input_path, output_path,
                gpp_controls_lookup, prompt_instruction, enhanced_schema, ai_client,
            )

    tasks = []

    for filename in os.listdir(SDT_PROFILES_PROCESS_DIR):
        if filename.endswith(".json") and not filename.endswith("_enhanced.json"):
            tasks.append(process_single_file(filename))

    if tasks:
        await asyncio.gather(*tasks)
    else:
        logger.info("No process profiles found to enhance.")

    logger.info("Finished Stage: Base Process Enhanced Profile Generation")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(run_stage_base_process_enhanced())