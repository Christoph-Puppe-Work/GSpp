import json
import os
import unittest

from pipeline.stage_ed23_anforderungen import (
    build_ed23_corpus,
    _corpus_text,
    _filter_matches,
)

MOCK_BSI = os.path.join(os.path.dirname(__file__), "mock_bsi_2023.json")


class TestBuildEd23Corpus(unittest.TestCase):
    def setUp(self):
        with open(MOCK_BSI, encoding="utf-8") as f:
            self.catalog = json.load(f)
        self.stripped, self.lookup = build_ed23_corpus(self.catalog)

    def test_extracts_every_anforderung(self):
        ids = {a["id"] for a in self.stripped}
        self.assertIn("ISMS.1.A1", ids)
        self.assertIn("SYS.1.1.A1", ids)

    def test_entries_have_name_and_prose(self):
        entry = next(a for a in self.stripped if a["id"] == "SYS.1.1.A1")
        self.assertEqual(entry["name"], "BSI Test Control (SYS)")
        self.assertTrue(entry["prose"])  # statement prose captured
        self.assertNotIn("\n", entry["prose"])  # newlines flattened

    def test_lookup_keyed_by_normalized_id(self):
        # normalize_id lowercases + strips, so a messy id still resolves.
        self.assertEqual(self.lookup["sys.1.1.a1"]["id"], "SYS.1.1.A1")

    def test_corpus_text_is_one_line_per_anforderung(self):
        text = _corpus_text(self.stripped)
        self.assertEqual(len(text.splitlines()), len(self.stripped))
        self.assertIn("SYS.1.1.A1 | BSI Test Control (SYS) |", text)


class TestFilterMatches(unittest.TestCase):
    def setUp(self):
        with open(MOCK_BSI, encoding="utf-8") as f:
            catalog = json.load(f)
        _, self.lookup = build_ed23_corpus(catalog)

    def test_drops_hallucinated_ids_and_restores_canonical(self):
        raw = [
            {"id": " sys.1.1.a1 ", "name": "wrong name from model", "begruendung": "passt"},
            {"id": "FAKE.9.A99", "name": "Hallucinated", "begruendung": "erfunden"},
        ]
        result = _filter_matches(raw, self.lookup)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "SYS.1.1.A1")  # canonical casing restored
        self.assertEqual(result[0]["name"], "BSI Test Control (SYS)")  # canonical name, not model's
        self.assertEqual(result[0]["begruendung"], "passt")

    def test_dedupes_repeated_ids(self):
        raw = [
            {"id": "SYS.1.1.A1", "name": "x", "begruendung": "a"},
            {"id": "sys.1.1.a1", "name": "y", "begruendung": "b"},
        ]
        self.assertEqual(len(_filter_matches(raw, self.lookup)), 1)

    def test_non_list_returns_empty(self):
        self.assertEqual(_filter_matches({"id": "SYS.1.1.A1"}, self.lookup), [])
        self.assertEqual(_filter_matches(None, self.lookup), [])


if __name__ == "__main__":
    unittest.main()
