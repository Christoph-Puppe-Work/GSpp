import re

with open('Gpp-ai-tool/src/pipeline/stage_base_process_enhanced.py', 'r') as f:
    content = f.read()

# Update the docstring
content = re.sub(
    r'Pipeline Stage: ED2023 Enhanced Profile Generation.*?One enhanced profile is written per Baustein to ED23_PROFILES_DIR\.',
    'Pipeline Stage: Base Process Enhanced Profile Generation\n\nThis stage takes the process profiles from `SDT_PROFILES_PROCESS_DIR`\nand enriches every control with AI-generated maturity sub-statements (levels 1-5)\nplus classifications (NIST class, ISMS phase, CIA), emitted as OSCAL `alter` blocks.\nThe enhanced profile is written back to the same directory with `_enhanced.json` appended.',
    content, flags=re.DOTALL
)

# Update run_stage_base_process_enhanced function
run_func_new = """async def run_stage_base_process_enhanced():
    \"\"\"Executes the Base Process enhanced profile generation stage.\"\"\"
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
    asyncio.run(run_stage_base_process_enhanced())"""

# Find where async def run_stage_base_process_enhanced() starts and replace it all
start_idx = content.find("async def run_stage_base_process_enhanced():")
if start_idx != -1:
    content = content[:start_idx] + run_func_new

with open('Gpp-ai-tool/src/pipeline/stage_base_process_enhanced.py', 'w') as f:
    f.write(content)
