"""Schema-contract guards for the maker-checker validation path."""

import jsonschema
import pytest

from GS_backend_MCP.myserver.main import OSCAL_ROOT_KEYS, SCHEMA_CACHE
from GS_backend_MCP.myserver.gcp.storage import OscalModel


@pytest.mark.parametrize("model", list(OscalModel))
def test_root_key_matches_schema_required(model: OscalModel) -> None:
    """OSCAL_ROOT_KEYS must agree with each schema's required top-level key —
    a mismatch wraps payloads under the wrong key and every create/update
    fails with "'<root>' is a required property"."""
    schema = SCHEMA_CACHE[model]
    assert schema.get("required") == [OSCAL_ROOT_KEYS[model]]


@pytest.mark.parametrize("model", list(OscalModel))
def test_schemas_compile_under_python_re(model: OscalModel) -> None:
    """The loaded schemas must pass the metaschema check — i.e. all XSD
    regex classes (\\p{L}, \\p{N}) were translated to Python-compatible
    patterns at load time."""
    jsonschema.Draft7Validator.check_schema(SCHEMA_CACHE[model])
