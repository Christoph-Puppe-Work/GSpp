"""
Manages the import of environment variables for the application.

This module retrieves configuration settings from the environment, providing
a single source of truth for all configurable parameters. It includes type
casting and default values to ensure robustness.
"""

import os
from typing import Optional


class AppConfig:
    """A dataclass-like container for application configuration."""

    def __init__(self):
        # Vertex AI / Gemini access (the only external service the pipeline still uses).
        self.gcp_project_id: Optional[str] = os.environ.get("GCP_PROJECT_ID")
        self.region: Optional[str] = os.environ.get("REGION", "global")
        # Optional Vertex AI endpoint/model override. The model id otherwise comes from
        # constants.GROUND_TRUTH_MODEL, so this is not required to start the tool.
        self.ai_endpoint_id: Optional[str] = os.environ.get("AI_ENDPOINT_ID")
        self.is_test_mode: bool = os.environ.get("TEST", "false").lower() == "true"
        self.overwrite_temp_files: bool = (
            os.environ.get("OVERWRITE_TEMP_FILES", "false").lower() == "true"
        )
        self.max_concurrent_ai_requests: int = int(
            os.environ.get("MAX_CONCURRENT_AI_REQUESTS", "5")
        )
        # TTL for explicit Vertex context caches. The default (60 min) can elapse before a
        # full G++ run finishes, expiring the cache mid-stage; 4h comfortably outlives a run.
        self.context_cache_ttl_seconds: int = int(
            os.environ.get("CONTEXT_CACHE_TTL_SECONDS", "14400")
        )

        if not self.is_test_mode:
            self._validate_production_config()

    def _validate_production_config(self):
        """Ensures the required variables are set in a non-test environment.

        Only `GCP_PROJECT_ID` is genuinely required: the pipeline fetches inputs from
        GitHub and writes outputs to local directories, so the former GCS variables
        (BUCKET_NAME / SOURCE_PREFIX / OUTPUT_PREFIX) are no longer read and are not
        validated. AI_ENDPOINT_ID is optional (see __init__).
        """
        required_vars = {
            "GCP_PROJECT_ID": self.gcp_project_id,
        }
        missing_vars = [key for key, value in required_vars.items() if value is None]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )


# Create a single, importable instance of the AppConfig.
app_config = AppConfig()
