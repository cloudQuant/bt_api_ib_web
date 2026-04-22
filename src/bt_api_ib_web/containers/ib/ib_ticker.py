from __future__ import annotations

from typing import Any

from bt_api_ib_web.containers.ib._base import _IbContainerBase, _to_float, _to_int


class IbTickerData(_IbContainerBase):
    def __init__(
        self,
        ticker_info: Any,
        symbol_name: Any = None,
        asset_type: Any = "STK",
        has_been_json_encoded: Any = False,
    ) -> None:
        super().__init__(
            "ticker_info",
            ticker_info,
            symbol_name=symbol_name,
            asset_type=asset_type,
            has_been_json_encoded=has_been_json_encoded,
        )
        self.ticker_info = ticker_info
        self.contract_symbol: str | None = None
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
        if self._initialized:
            return self
        info = self.ticker_info if isinstance(self.ticker_info, dict) else {}
        self.contract_symbol = info.get("symbol", self.symbol_name)
        self.bid_val = float(info["bid"]) if info.get("bid") is not None else None
        self.ask_val = float(info["ask"]) if info.get("ask") is not None else None
        self.bid_size_val = _to_float(info.get("bidSize"))
        self.ask_size_val = _to_float(info.get("askSize"))
        self.last_val = float(info["last"]) if info.get("last") is not None else None
        self.last_size_val = _to_float(info.get("lastSize"))
        self.volume_val = _to_int(info.get("volume"))
        self.high_val = float(info["high"]) if info.get("high") is not None else None
        self.low_val = float(info["low"]) if info.get("low") is not None else None
        self.close_val = float(info["close"]) if info.get("close") is not None else None
        self.timestamp_val = info.get("time")
        self._initialized = True
        return self

    def get_local_update_time(self) -> float:
        return float(self.timestamp_val) if isinstance(self.timestamp_val, (int, float)) else 0.0

    def get_symbol_name(self) -> str:
        return str(self.contract_symbol or self.symbol_name or "")

    def get_ticker_symbol_name(self) -> str | None:
        return self.contract_symbol or self.symbol_name

    def get_asset_type(self) -> str:
        return str(self.asset_type)

    def get_server_time(self) -> float | None:
        return float(self.timestamp_val) if isinstance(self.timestamp_val, (int, float)) else None

    def get_bid_price(self) -> float | None:
        return self.bid_val

    def get_ask_price(self) -> float | None:
        return self.ask_val

    def get_bid_volume(self) -> float | None:
        return self.bid_size_val

    def get_ask_volume(self) -> float | None:
        return self.ask_size_val

    def get_last_price(self) -> float | None:
        return self.last_val

    def get_last_volume(self) -> float | None:
        return self.last_size_val

    def get_all_data(self) -> dict[str, Any]:
        return {
            "exchange_name": self.exchange_name,
            "symbol": self.contract_symbol,
            "bid": self.bid_val,
            "ask": self.ask_val,
            "bid_size": self.bid_size_val,
            "ask_size": self.ask_size_val,
            "last": self.last_val,
            "last_size": self.last_size_val,
            "volume": self.volume_val,
            "high": self.high_val,
            "low": self.low_val,
            "close": self.close_val,
            "time": self.timestamp_val,
        }
