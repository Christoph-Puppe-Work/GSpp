import pytest
from agents.orchestrator import _extract_iv_id

def test_extract_iv_id():
    assert _extract_iv_id("user123::iv::iv-12345") == "iv-12345"
    assert _extract_iv_id("user123") == "unknown-iv"
    assert _extract_iv_id("::iv::iv-67890") == "iv-67890"

def test_extract_iv_id_edge_cases():
    assert _extract_iv_id("") == "unknown-iv"
    assert _extract_iv_id("no-separator") == "unknown-iv"
    assert _extract_iv_id("multiple::iv::iv-1::iv::iv-2") == "unknown-iv" # Split gives length 3
