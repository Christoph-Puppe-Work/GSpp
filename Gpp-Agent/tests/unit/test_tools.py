import unittest
from tools.exit_loop import exit_loop
from unittest.mock import MagicMock

class TestTools(unittest.TestCase):
    def test_exit_loop(self):
        tool_context = MagicMock()
        tool_context.actions = MagicMock()

        result = exit_loop(reason="Looks good", tool_context=tool_context)

        self.assertEqual(result["status"], "approved")
        self.assertEqual(tool_context.actions.escalate, True)

if __name__ == "__main__":
    unittest.main()
