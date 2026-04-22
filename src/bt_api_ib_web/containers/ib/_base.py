from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float:
    return float(value or 0)


def _to_int(value: Any) -> int:
    return int(value or 0)


class _IbContainerBase:
    exchange_name = 'IB'

    def __init__(
        self,
        payload_name: str,
        payload: Any,
        *,
        symbol_name: Any = None,
        asset_type: Any = 'STK',
        has_been_json_encoded: Any = False,
    ) -> None:
        setattr(self, payload_name, payload)
        self.event = payload
        self.symbol_name = symbol_name
        self.asset_type = asset_type
        self.has_been_json_encoded = has_been_json_encoded
        self._initialized = False

    def get_exchange_name(self) -> str:
        return str(self.exchange_name)
