import unittest
from orchestrator.agent import set_informationsverbund
from unittest.mock import MagicMock

class TestOrchestratorTools(unittest.TestCase):
    def test_set_informationsverbund_valid(self):
        tool_context = MagicMock()
        tool_context.state = {}
        tool_context.user_id = "user1"

        result = set_informationsverbund("iv-test-customer", tool_context)

        self.assertIn("Informationsverbund set to iv-test-customer", result)
        self.assertEqual(tool_context.state["informationsverbund_id"], "iv-test-customer")

    def test_set_informationsverbund_invalid(self):
        tool_context = MagicMock()
        tool_context.state = {}

        result = set_informationsverbund("bad_id", tool_context)

        self.assertIn("Error: Invalid IV-ID format", result)
        self.assertNotIn("informationsverbund_id", tool_context.state)

if __name__ == "__main__":
    unittest.main()
