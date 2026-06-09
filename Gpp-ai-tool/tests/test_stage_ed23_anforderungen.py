import json
import os
import unittest

from pipeline.stage_ed23_anforderungen import (
    build_ed23_corpus,
    _corpus_text,
    _filter_matches,
)
from utils.oscal_mapping import to_oscal_mapping_collection

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


class TestToOscalMappingCollection(unittest.TestCase):
    def setUp(self):
        self.sample = {
            "GC.1.1": [
                {"id": "ISMS.1.A1", "name": "Übernahme der Gesamtverantwortung", "begruendung": "passt thematisch"},
                {"id": "ORP.1.A1", "name": "Festlegung von Verantwortlichkeiten", "begruendung": "ergänzt"},
            ],
            "GC.2.1": [
                {"id": "SYS.1.1.A1", "name": "BSI Test Control (SYS)", "begruendung": ""},
            ],
            "GC.9.9": [],  # a control with no matches contributes no map entries
        }
        self.doc = to_oscal_mapping_collection(
            self.sample, last_modified="2026-01-01T00:00:00+00:00", version="2026-01-01"
        )
        self.mc = self.doc["mapping-collection"]

    def test_root_and_metadata(self):
        self.assertIn("mapping-collection", self.doc)
        self.assertTrue(self.mc["uuid"])
        self.assertEqual(self.mc["metadata"]["oscal-version"], "1.2.2")
        self.assertEqual(self.mc["metadata"]["version"], "2026-01-01")
        self.assertTrue(self.mc["metadata"]["title"])

    def test_provenance_uses_valid_tokens(self):
        prov = self.mc["provenance"]
        self.assertEqual(prov["method"], "automation")            # human|automation|hybrid
        self.assertEqual(prov["matching-rationale"], "semantic")  # syntactic|semantic|functional
        self.assertEqual(prov["status"], "draft")                 # complete|not-complete|draft|...
        self.assertTrue(prov["mapping-description"])               # required markup-multiline

    def test_single_mapping_with_catalog_resources(self):
        self.assertEqual(len(self.mc["mappings"]), 1)
        mp = self.mc["mappings"][0]
        self.assertEqual(mp["source-resource"]["type"], "catalog")
        self.assertEqual(mp["target-resource"]["type"], "catalog")
        self.assertTrue(mp["source-resource"]["href"])
        self.assertTrue(mp["target-resource"]["href"])

    def test_one_map_per_pair(self):
        # 2 (GC.1.1) + 1 (GC.2.1) + 0 (GC.9.9) = 3
        self.assertEqual(len(self.mc["mappings"][0]["maps"]), 3)

    def test_map_shape_name_and_begruendung(self):
        maps = self.mc["mappings"][0]["maps"]
        by_target = {m["targets"][0]["id-ref"]: m for m in maps}
        m = by_target["ISMS.1.A1"]
        self.assertEqual(m["relationship"], "intersects-with")
        self.assertEqual(m["sources"][0], {"type": "control", "id-ref": "GC.1.1"})
        self.assertEqual(m["targets"][0]["type"], "control")
        self.assertEqual(
            m["targets"][0]["props"][0],
            {"name": "label", "value": "Übernahme der Gesamtverantwortung"},
        )
        self.assertEqual(m["remarks"], "passt thematisch")

    def test_empty_begruendung_omits_remarks(self):
        maps = self.mc["mappings"][0]["maps"]
        m = next(m for m in maps if m["targets"][0]["id-ref"] == "SYS.1.1.A1")
        self.assertNotIn("remarks", m)

    def test_deterministic_output(self):
        again = to_oscal_mapping_collection(
            self.sample, last_modified="2026-01-01T00:00:00+00:00", version="2026-01-01"
        )
        self.assertEqual(json.dumps(self.doc, sort_keys=True), json.dumps(again, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
