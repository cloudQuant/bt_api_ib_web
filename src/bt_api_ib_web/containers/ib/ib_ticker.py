"""Module-level docstring."""
from __future__ import annotations

from typing import Any

from bt_api_ib_web.containers.ib._base import _IbContainerBase, _to_float, _to_int


class IbTickerData(_IbContainerBase):
    """Class IbTickerData"""
    def __init__(
        self,
        ticker_info: Any,
        symbol_name: Any = None,
        asset_type: Any = 'STK',
        has_been_json_encoded: Any = False,
    ) -> None:
        """__init__ method"""
        super().__init__(
            'ticker_info',
            ticker_info,
            symbol_name=symbol_name,
            asset_type=asset_type,
            has_been_json_encoded=has_been_json_encoded,
        )
        self.ticker_info = ticker_info
        self.contract_symbol: str | None = None
        self.instrument_id: str | None = None
        self.exchange_id: str | None = None
        self.bid_val: float | None = None
        self.ask_val: float | None = None
        self.bid_size_val: float | None = None
        self.ask_size_val: float | None = None
        self.last_val: float | None = None
        self.last_size_val: float | None = None
        self.volume_val: int | None = None
        self.high_val: float | None = None
        self.low_val: float | None = None
        self.close_val: float | None = None
        self.timestamp_val: float | str | None = None

    def init_data(self) -> IbTickerData:
        """init_data method"""
        if self._initialized:
            return self
        info = self.ticker_info if isinstance(self.ticker_info, dict) else {}
        conid = _first_value(info, 'conidEx', 'conid', 'contract_id') or _topic_conid(
            info.get('topic')
        )
        self.instrument_id = str(conid) if conid not in (None, '') else None
        self.contract_symbol = str(
            _first_value(info, 'symbol')
            or self.symbol_name
            or self.instrument_id
            or ''
        ) or None
        self.exchange_id = _first_text(info, 'exchange', 'listingExchange') or None
        self.bid_val = _optional_float(info, 'bid', '84', 'bidPrice')
        self.ask_val = _optional_float(info, 'ask', '86', 'askPrice')
        self.bid_size_val = _optional_float(info, 'bidSize', '85', 'bid_volume')
        self.ask_size_val = _optional_float(info, 'askSize', '88', 'ask_volume')
        self.last_val = _optional_float(info, 'last', '31', 'lastPrice')
        self.last_size_val = _optional_float(info, 'lastSize')
        self.volume_val = _optional_int(info, 'volume', '87')
        self.high_val = _optional_float(info, 'high', 'highPrice')
        self.low_val = _optional_float(info, 'low', 'lowPrice')
        self.close_val = _optional_float(info, 'close', 'closePrice')
        self.timestamp_val = info.get('time')
        self._initialized = True
        return self

    def get_local_update_time(self) -> float:
        """get_local_update_time method"""
        return (
            float(self.timestamp_val)
            if isinstance(self.timestamp_val, (int, float))
            else 0.0
        )

    def get_symbol_name(self) -> str:
        """get_symbol_name method"""
        return str(self.contract_symbol or self.symbol_name or '')

    def get_ticker_symbol_name(self) -> str | None:
        """get_ticker_symbol_name method"""
        return self.contract_symbol or self.symbol_name

    def get_asset_type(self) -> str:
        """get_asset_type method"""
        return str(self.asset_type)

    def get_server_time(self) -> float | None:
        """get_server_time method"""
        return (
            float(self.timestamp_val)
            if isinstance(self.timestamp_val, (int, float))
            else None
        )

    def get_bid_price(self) -> float | None:
        """get_bid_price method"""
        return self.bid_val

    def get_ask_price(self) -> float | None:
        """get_ask_price method"""
        return self.ask_val

    def get_bid_volume(self) -> float | None:
        """get_bid_volume method"""
        return self.bid_size_val

    def get_ask_volume(self) -> float | None:
        """get_ask_volume method"""
        return self.ask_size_val

    def get_last_price(self) -> float | None:
        """get_last_price method"""
        return self.last_val

    def get_last_volume(self) -> float | None:
        """get_last_volume method"""
        return self.last_size_val

    def get_all_data(self) -> dict[str, Any]:
        """get_all_data method"""
        return {
            'exchange_name': self.exchange_name,
            'symbol': self.contract_symbol,
            'instrument_id': self.instrument_id,
            'exchange_id': self.exchange_id,
            'bid': self.bid_val,
            'ask': self.ask_val,
            'bid_size': self.bid_size_val,
            'ask_size': self.ask_size_val,
            'last': self.last_val,
            'last_size': self.last_size_val,
            'volume': self.volume_val,
            'high': self.high_val,
            'low': self.low_val,
            'close': self.close_val,
            'time': self.timestamp_val,
        }

    def get_market_projection(self) -> dict[str, Any]:
        """Project a direct IB Web market row without emitting or caching it."""
        self.init_data()
        return {
            'exchange_name': self.exchange_name,
            'symbol': self.contract_symbol,
            'instrument_id': self.instrument_id,
            'exchange_id': self.exchange_id,
            'asset_type': str(self.asset_type).lower(),
            'timestamp': self.timestamp_val,
            'price': self.last_val if self.last_val is not None else 0.0,
            'last_price': self.last_val,
            'bid_price': self.bid_val,
            'ask_price': self.ask_val,
            'bid_volume': self.bid_size_val,
            'ask_volume': self.ask_size_val,
            'volume': self.volume_val if self.volume_val is not None else 0,
        }


def _first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value is not None and value != '':
            return value
    return None


def _first_text(payload: dict[str, Any], *keys: str) -> str:
    value = _first_value(payload, *keys)
    return str(value or '').strip()


def _optional_float(payload: dict[str, Any], *keys: str) -> float | None:
    value = _first_value(payload, *keys)
    if value is None or isinstance(value, bool):
        return None
    try:
        return _to_float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(payload: dict[str, Any], *keys: str) -> int | None:
    value = _first_value(payload, *keys)
    if value is None or isinstance(value, bool):
        return None
    try:
        return _to_int(value)
    except (TypeError, ValueError):
        return None


def _topic_conid(value: Any) -> Any:
    topic = str(value or '').strip()
    if topic.startswith('smd+'):
        parts = topic.split('+', 2)
        if len(parts) >= 2:
            return parts[1]
    return None
