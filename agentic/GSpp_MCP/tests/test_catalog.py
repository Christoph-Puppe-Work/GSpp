import pytest
from server.catalog import Catalog
from server.search import SearchIndex

import os

@pytest.fixture
def catalog():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    catalog_path = os.path.join(base_dir, "data", "Grundschutz++-catalog.json")
    mapping_path = os.path.join(base_dir, "data", "zielobjekt_controls.json")
    return Catalog(catalog_path, mapping_path)

def test_catalog_load(catalog):
    assert len(catalog.controls) > 0
    assert len(catalog.groups) > 0
    assert len(catalog.zielobjekt_map) > 0

def test_get_control(catalog):
    # Test with a known control ID from the catalog
    control_id = "ISMS.1.A1"
    control = catalog.get_control(control_id)
    assert control is not None
    assert control["id"] == control_id
    assert "title" in control

def test_search_index(catalog):
    index = SearchIndex()
    for control in catalog.list_controls():
        text = f"{control['id']} {control['title']} {control['prose']}"
        index.add_document(control['id'], text)

    # Search for a term likely to be in the catalog
    results = index.search("Sicherheit")
    assert len(results) > 0

def test_zielobjekt_mapping(catalog):
    categories = catalog.list_zielobjektkategorien()
    assert len(categories) > 0

    # Test for a known category from the mapping
    cat_id = categories[0]
    controls = catalog.controls_for_zielobjekt(cat_id)
    assert len(controls) > 0
