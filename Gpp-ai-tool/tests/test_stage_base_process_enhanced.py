import unittest
from unittest.mock import patch, MagicMock, mock_open
import asyncio
from pipeline.stage_base_process_enhanced import run_stage_base_process_enhanced

class TestStageBaseProcessEnhanced(unittest.IsolatedAsyncioTestCase):
    @patch('pipeline.stage_base_process_enhanced.create_dir_if_not_exists')
    @patch('pipeline.stage_base_process_enhanced.read_json_file')
    @patch('pipeline.stage_base_process_enhanced.os.listdir')
    @patch('pipeline.stage_base_process_enhanced.generate_enhanced_profile')
    @patch('pipeline.stage_base_process_enhanced.extract_all_gpp_controls')
    @patch('pipeline.stage_base_process_enhanced.AiClient')
    async def test_run_stage_base_process_enhanced(self, mock_ai_client, mock_extract, mock_generate, mock_listdir, mock_read_json, mock_create_dir):
        # Setup mocks
        mock_read_json.side_effect = [
            {"catalog": {"groups": []}}, # GPP_KOMPENDIUM_JSON_PATH
            {"generate_enhanced_controls_prompt": "test_prompt"}, # PROMPT_CONFIG_PATH
            {"type": "object"} # ENHANCED_CONTROL_RESPONSE_SCHEMA_PATH
        ]

        mock_extract.return_value = {"SENS.1.2": {"title": "Title"}}

        # Test file processing filter
        mock_listdir.return_value = [
            "Methodik.json",
            "SENS_prozesse.json",
            "OPS.1.2.json",
            "not_a_json.txt",
            "Already_enhanced.json_enhanced.json",
            "Methodik_enhanced.json"
        ]

        # Call the async function
        await run_stage_base_process_enhanced()

        # Should only be called for the 3 normal .json files
        self.assertEqual(mock_generate.call_count, 3)

        # Extract names from calls
        calls = mock_generate.call_args_list
        baustein_titles = [call.args[1] for call in calls]

        self.assertIn("Methodik", baustein_titles)
        self.assertIn("SENS_prozesse", baustein_titles)
        self.assertIn("OPS.1.2", baustein_titles)

if __name__ == '__main__':
    unittest.main()
