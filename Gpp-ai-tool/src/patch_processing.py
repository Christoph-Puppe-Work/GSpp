import re

with open('Gpp-ai-tool/src/pipeline/processing.py', 'r') as f:
    content = f.read()

# Add import
content = content.replace(
    "from pipeline import stage_strip, stage_gpp, stage_match_bausteine, stage_profiles, stage_ED23_profiles_enhanced",
    "from pipeline import stage_strip, stage_gpp, stage_match_bausteine, stage_profiles, stage_ED23_profiles_enhanced, stage_base_process_enhanced"
)

# Add stage 6
replacement = """        # Stage 5: Generate ED2023 enhanced profiles (per Baustein).
        logger.info("--- STAGE: ED23_PROFILES_ENHANCED ---")
        logger.info("Starting: Generating ED2023 enhanced profiles.")
        await stage_ED23_profiles_enhanced.run_stage_ED23_profiles_enhanced()
        logger.info("--- STAGE: ED23_PROFILES_ENHANCED - COMPLETE ---")

        # Stage 6: Generate base process enhanced profiles.
        logger.info("--- STAGE: BASE_PROCESS_ENHANCED ---")
        logger.info("Starting: Generating base process enhanced profiles.")
        await stage_base_process_enhanced.run_stage_base_process_enhanced()
        logger.info("--- STAGE: BASE_PROCESS_ENHANCED - COMPLETE ---")"""

content = content.replace(
    """        # Stage 5: Generate ED2023 enhanced profiles (per Baustein).
        logger.info("--- STAGE: ED23_PROFILES_ENHANCED ---")
        logger.info("Starting: Generating ED2023 enhanced profiles.")
        await stage_ED23_profiles_enhanced.run_stage_ED23_profiles_enhanced()
        logger.info("--- STAGE: ED23_PROFILES_ENHANCED - COMPLETE ---")""",
    replacement
)

with open('Gpp-ai-tool/src/pipeline/processing.py', 'w') as f:
    f.write(content)
