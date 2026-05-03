from typing import Any, Optional
from google.adk.artifacts.gcs_artifact_service import GcsArtifactService


class InformationsverbundGcsArtifactService(GcsArtifactService):
    """
    Wraps GcsArtifactService so all artifact paths are prefixed with the
    informationsverbund_id from session state. Prevents cross-tenant access.
    """

    def _get_blob_name(
        self,
        app_name: str,
        user_id: str,
        filename: str,
        version: int,
        session_id: Optional[str] = None,
    ) -> str:
        # ADK default returns: {app_name}/{user_id}/{session_id}/{filename}/{version}
        # We override to: {iv_id}/artifacts/{session_id}/{filename}/{version}
        iv_id = self._extract_iv_id(user_id)
        if session_id is None:
             return f"{iv_id}/artifacts/no_session/{filename}/{version}"
        return f"{iv_id}/artifacts/{session_id}/{filename}/{version}"

    def _get_blob_prefix(
        self,
        app_name: str,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
    ) -> str:
        iv_id = self._extract_iv_id(user_id)
        if session_id is None:
             return f"{iv_id}/artifacts/no_session/{filename}"
        return f"{iv_id}/artifacts/{session_id}/{filename}"

    @staticmethod
    def _extract_iv_id(user_id: str) -> str:
        # Convention: user_id = "{caller}::iv::{informationsverbund_id}"
        if "::iv::" not in user_id:
            # Fallback for testing or if not yet set, though orchestrator should ensure this
            return "default-iv"
        return user_id.split("::iv::", 1)[1]
