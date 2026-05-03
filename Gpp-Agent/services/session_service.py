import json
import time
from typing import Any, List, Optional
from google.adk.sessions.base_session_service import BaseSessionService, ListSessionsResponse, GetSessionConfig
from google.adk.sessions.session import Session
from google.cloud import storage


class InformationsverbundSessionService(BaseSessionService):
    """
    GCS-based SessionService that namespaces sessions by informationsverbund_id.
    """

    def __init__(self, bucket_name: str):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

    def _extract_iv_id(self, user_id: str) -> str:
        if "::iv::" not in user_id:
            return "default-iv"
        return user_id.split("::iv::", 1)[1]

    def _get_session_path(self, user_id: str, session_id: str) -> str:
        iv_id = self._extract_iv_id(user_id)
        return f"{iv_id}/sessions/{session_id}.json"

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        if not session_id:
            session_id = str(int(time.time() * 1000))

        session = Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state or {},
            events=[],
            last_update_time=time.time()
        )
        await self._save_session(session)
        return session

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        path = self._get_session_path(user_id, session_id)
        blob = self.bucket.blob(path)
        if not blob.exists():
            return None

        data = json.loads(blob.download_as_text())
        return Session(**data)

    async def list_sessions(
        self, *, app_name: str, user_id: Optional[str] = None
    ) -> ListSessionsResponse:
        prefix = ""
        if user_id:
            iv_id = self._extract_iv_id(user_id)
            prefix = f"{iv_id}/sessions/"

        blobs = self.bucket.list_blobs(prefix=prefix)
        sessions = []
        for blob in blobs:
            if blob.name.endswith(".json"):
                data = json.loads(blob.download_as_text())
                # v1 schemas use slightly different field names in dict
                # but Session(**data) should work if data is correct
                sessions.append(Session(**data))

        return ListSessionsResponse(sessions=sessions)

    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        path = self._get_session_path(user_id, session_id)
        blob = self.bucket.blob(path)
        if blob.exists():
            blob.delete()

    async def _save_session(self, session: Session) -> None:
        path = self._get_session_path(session.user_id, session.id)
        blob = self.bucket.blob(path)
        session.last_update_time = time.time()
        blob.upload_from_string(session.model_dump_json())

    async def append_event(self, session: Session, event: Any) -> Any:
        # Call base class to update in-memory state and events
        result = await super().append_event(session, event)
        # Persist the updated session
        await self._save_session(session)
        return result
