import logging
from types import SimpleNamespace

import pytest

from myserver.utils import get_iv_id


def _ctx_with_user_id(user_id: str | None):
    return SimpleNamespace(
        request_context=SimpleNamespace(
            session=SimpleNamespace(user_id=user_id),
        )
    )


def test_get_iv_id_from_session_user_id():
    ctx = _ctx_with_user_id("agent::iv::bank-ssp")

    assert get_iv_id(ctx) == "bank-ssp"


def test_get_iv_id_rejects_malformed_user_id_without_dev_fallback(monkeypatch):
    monkeypatch.delenv("GPP_BACKEND_ALLOW_DEV_IV_FALLBACK", raising=False)
    monkeypatch.delenv("GPP_BACKEND_DEV_IV_ID", raising=False)

    with pytest.raises(ValueError, match="Missing or malformed iv_id"):
        get_iv_id(_ctx_with_user_id("user"))


def test_get_iv_id_uses_explicit_dev_fallback(monkeypatch):
    monkeypatch.setenv("GPP_BACKEND_ALLOW_DEV_IV_FALLBACK", "1")
    monkeypatch.setenv("GPP_BACKEND_DEV_IV_ID", "local-dev")

    assert get_iv_id(_ctx_with_user_id("user")) == "local-dev"


def test_get_iv_id_uses_dev_fallback_when_session_context_missing(monkeypatch):
    monkeypatch.setenv("GPP_BACKEND_ALLOW_DEV_IV_FALLBACK", "1")
    monkeypatch.setenv("GPP_BACKEND_DEV_IV_ID", "local-dev")

    assert get_iv_id(SimpleNamespace()) == "local-dev"


def test_get_iv_id_does_not_log_error_when_dev_fallback_is_allowed(
    monkeypatch,
    caplog,
):
    monkeypatch.setenv("GPP_BACKEND_ALLOW_DEV_IV_FALLBACK", "1")
    monkeypatch.setenv("GPP_BACKEND_DEV_IV_ID", "caplog-dev")

    with caplog.at_level(logging.DEBUG, logger="GppContextMCP.utils"):
        assert get_iv_id(SimpleNamespace()) == "caplog-dev"

    assert not [
        record
        for record in caplog.records
        if record.name == "GppContextMCP.utils" and record.levelno >= logging.ERROR
    ]
