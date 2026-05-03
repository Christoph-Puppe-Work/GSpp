import unittest
from unittest.mock import MagicMock, patch
from services.artifact_service import InformationsverbundGcsArtifactService

class TestArtifactService(unittest.TestCase):
    @patch("google.cloud.storage.Client")
    def setUp(self, mock_client):
        # Mocking the GcsArtifactService initialization which tries to create a storage.Client
        self.service = InformationsverbundGcsArtifactService(bucket_name="test-bucket")

    def test_extract_iv_id(self):
        self.assertEqual(self.service._extract_iv_id("user1::iv::iv-123"), "iv-123")
        self.assertEqual(self.service._extract_iv_id("user1"), "default-iv")

    def test_get_blob_name(self):
        path = self.service._get_blob_name(
            app_name="app",
            user_id="caller::iv::iv-customer",
            filename="test.json",
            version=1,
            session_id="sess-456"
        )
        self.assertEqual(path, "iv-customer/artifacts/sess-456/test.json/1")

if __name__ == "__main__":
    unittest.main()
