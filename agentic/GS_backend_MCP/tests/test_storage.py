import pytest
from unittest.mock import MagicMock, patch
from myserver.gcp import storage
from myserver.gcp.storage import OscalModel

@patch("myserver.gcp.storage.get_storage_client")
def test_list_models(mock_get_client):
    iv_id = "test-iv"
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_iterator = MagicMock()
    mock_iterator.prefixes = ["ivs/test-iv/ssp/", "ivs/test-iv/catalog/", "ivs/test-iv/invalid/"]
    mock_client.list_blobs.return_value = mock_iterator

    models = storage.list_models(iv_id)

    assert "ssp" in models
    assert "catalog" in models
    assert "invalid" not in models
    assert len(models) == 2

    mock_client.list_blobs.assert_called_once_with(
        storage.BUCKET_NAME, prefix=f"ivs/{iv_id}/", delimiter='/'
    )
