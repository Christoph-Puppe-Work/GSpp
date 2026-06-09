"""
Core data processing logic for the OSCAL generation pipeline.

This module contains the orchestrator function for running the entire pipeline
from start to finish, executing each stage in the correct sequence.
"""

import logging
from pipeline import stage_gpp, stage_match_bausteine, stage_profiles, stage_ED23_profiles_enhanced, stage_base_process_enhanced, stage_ed23_anforderungen

logger = logging.getLogger(__name__)


async def run_full_pipeline() -> None:
    """
    Executes the entire data processing and OSCAL generation pipeline.

    This function orchestrates the full, end-to-end pipeline, running each
    stage in the required order to ensure data dependencies are met.
    """
    logger.info("--- Starting Full Pipeline Execution ---")

    try:
        # Stage 1: Process G++ Kompendium and create deterministic mappings.
        logger.info("--- STAGE: GPP ---")
        stage_gpp.run_stage_gpp()
        logger.info("--- STAGE: GPP - COMPLETE ---")

        # Stage 2: Perform high-level Baustein-to-Zielobjekt mapping.
        logger.info("--- STAGE: MATCH BAUSTEINE ---")
        await stage_match_bausteine.run_stage_match_bausteine()
        logger.info("--- STAGE: MATCH BAUSTEINE - COMPLETE ---")

        # Stage 3: Generate the base OSCAL profiles for each Zielobjekt.
        logger.info("--- STAGE: PROFILES ---")
        stage_profiles.run_stage_profiles()
        logger.info("--- STAGE: PROFILES - COMPLETE ---")

        # Stage 4: Generate ED2023 enhanced profiles (per Baustein).
        logger.info("--- STAGE: ED23_PROFILES_ENHANCED ---")
        logger.info("Starting: Generating ED2023 enhanced profiles.")
        await stage_ED23_profiles_enhanced.run_stage_ED23_profiles_enhanced()
        logger.info("--- STAGE: ED23_PROFILES_ENHANCED - COMPLETE ---")

        # Stage 5: Generate base process enhanced profiles.
        logger.info("--- STAGE: BASE_PROCESS_ENHANCED ---")
        logger.info("Starting: Generating base process enhanced profiles.")
        await stage_base_process_enhanced.run_stage_base_process_enhanced()
        logger.info("--- STAGE: BASE_PROCESS_ENHANCED - COMPLETE ---")

        # Stage 6: Map each G++ control to its matching BSI ED2023 Anforderungen.
        logger.info("--- STAGE: ED23_ANFORDERUNGEN ---")
        await stage_ed23_anforderungen.run_stage_ed23_anforderungen()
        logger.info("--- STAGE: ED23_ANFORDERUNGEN - COMPLETE ---")



    except Exception as e:
        logger.critical("A critical error occurred during the full pipeline execution.", exc_info=True)
        # Re-raise the exception to ensure the script exits with a non-zero status code.
        raise
    
    logger.info("--- Full Pipeline Execution Finished Successfully ---")