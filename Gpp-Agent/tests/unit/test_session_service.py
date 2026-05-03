import unittest
import asyncio
from unittest.mock import MagicMock, patch
from services.session_service import InformationsverbundSessionService

class TestSessionService(unittest.TestCase):
    @patch("google.cloud.storage.Client")
    def setUp(self, mock_client):
        self.service = InformationsverbundSessionService(bucket_name="test-bucket")
        self.service.bucket = MagicMock()
        self.mock_bucket = self.service.bucket

    def test_extract_iv_id(self):
        self.assertEqual(self.service._extract_iv_id("u::iv::iv-2"), "iv-2")
        self.assertEqual(self.service._extract_iv_id("u"), "default-iv")

    def test_get_session_path(self):
        path = self.service._get_session_path("caller::iv::iv-cust", "sess1")
        self.assertEqual(path, "iv-cust/sessions/sess1.json")

    @patch("google.cloud.storage.Client")
    def test_create_session(self, mock_client):
        # Using a sync wrapper for the async call to avoid complex async test setup for now
        async def run_test():
            session = await self.service.create_session(
                app_name="app",
                user_id="user::iv::iv-1",
                session_id="s1"
            )
            return session

        session = asyncio.run(run_test())
        self.assertEqual(session.id, "s1")
        self.mock_bucket.blob.assert_called_with("iv-1/sessions/s1.json")

if __name__ == "__main__":
    unittest.main()
