import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from orchestrator.agent import root_agent
from agents.cis_oscal.workflow import get_workflow

class TestIntegration(unittest.TestCase):
    def test_workflow_initialization(self):
        # Verify that all workflows and agents can be initialized without errors
        root = root_agent()
        self.assertEqual(root.name, "root_orchestrator")
        self.assertEqual(len(root.sub_agents), 3)

        cis_workflow = get_workflow()
        self.assertEqual(cis_workflow.name, "cis_oscal_workflow")
        self.assertEqual(len(cis_workflow.sub_agents), 3)

if __name__ == "__main__":
    unittest.main()
