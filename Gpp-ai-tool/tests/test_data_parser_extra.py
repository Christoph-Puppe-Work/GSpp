import unittest
from utils.oscal_utils import extract_all_gpp_controls

class TestDataParserExtra(unittest.TestCase):
    def test_extract_all_gpp_controls_nested(self):
        """Test that controls are extracted recursively from nested groups."""
        mock_gpp_data = {
            "catalog": {
                "groups": [
                    {
                        "id": "group1",
                        "controls": [{"id": "G1.C1", "title": "Control 1"}],
                        "groups": [
                            {
                                "id": "subgroup1",
                                "controls": [{"id": "G1.S1.C1", "title": "Sub Control 1"}],
                                "groups": [
                                    {
                                        "id": "deepgroup1",
                                        "controls": [{"id": "G1.S1.D1.C1", "title": "Deep Control 1"}],
                                        "groups": [
                                            {
                                                "id": "superdeepgroup1",
                                                "controls": [{"id": "G1.S1.D1.S1.C1", "title": "Super Deep Control 1"}]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "id": "group2",
                        # Group 2 has no direct controls, only a subgroup
                        "groups": [
                            {
                                "id": "subgroup2",
                                "controls": [{"id": "G2.S2.C1", "title": "Sub Control 2"}]
                            }
                        ]
                    }
                ]
            }
        }

        controls = extract_all_gpp_controls(mock_gpp_data)

        self.assertIn("G1.C1", controls)
        self.assertIn("G1.S1.C1", controls)
        self.assertIn("G1.S1.D1.C1", controls)
        self.assertIn("G1.S1.D1.S1.C1", controls) # Check level 4 depth
        self.assertIn("G2.S2.C1", controls)

        self.assertEqual(controls["G1.C1"]["title"], "Control 1")
        self.assertEqual(controls["G1.S1.D1.C1"]["title"], "Deep Control 1")
        self.assertEqual(controls["G1.S1.D1.S1.C1"]["title"], "Super Deep Control 1")

    def test_extract_all_gpp_controls_nested_subcontrols(self):
        """Sub-controls nested inside a control must also be in the lookup with their
        statement_part_id (regression for the 'no statement part to anchor' warning)."""
        mock_gpp_data = {
            "catalog": {
                "groups": [
                    {
                        "id": "group1",
                        "controls": [
                            {
                                "id": "TEST.2.2",
                                "title": "Parent",
                                "parts": [{"name": "statement", "id": "TEST.2.2_stm", "prose": "Parent stmt"}],
                                "controls": [
                                    {
                                        "id": "TEST.2.2.1",
                                        "title": "Sub 1",
                                        "parts": [{"name": "statement", "id": "TEST.2.2.1_stm", "prose": "Sub stmt"}],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        }

        controls = extract_all_gpp_controls(mock_gpp_data)

        self.assertIn("TEST.2.2", controls)
        self.assertIn("TEST.2.2.1", controls)
        self.assertEqual(controls["TEST.2.2.1"]["statement_part_id"], "TEST.2.2.1_stm")
        self.assertEqual(controls["TEST.2.2.1"]["prose"], "Sub stmt")

    def test_extract_all_gpp_controls_empty(self):
        """Test with empty catalog."""
        mock_gpp_data = {"catalog": {"groups": []}}
        controls = extract_all_gpp_controls(mock_gpp_data)
        self.assertEqual(len(controls), 0)

if __name__ == "__main__":
    unittest.main()
