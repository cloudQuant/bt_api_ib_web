from __future__ import annotations

from importlib import import_module

import pytest


def test_legacy_gateway_adapter_module_is_not_shipped() -> None:
    with pytest.raises(ModuleNotFoundError) as exc_info:
        import_module("bt_api_ib_web.gateway.adapter")

    assert exc_info.value.name in {
        "bt_api_ib_web.gateway",
        "bt_api_ib_web.gateway.adapter",
    }
