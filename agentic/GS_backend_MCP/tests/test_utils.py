from types import SimpleNamespace

import pytest

from GS_backend_MCP.myserver.utils import get_iv_id


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


def test_get_iv_id_from_request_headers():
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            request=SimpleNamespace(
                headers={"x-gpp-user-id": "agent::iv::bank-ssp"}
            ),
            session=SimpleNamespace(user_id=None),
        )
    )

    assert get_iv_id(ctx) == "bank-ssp"

