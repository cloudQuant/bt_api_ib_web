from __future__ import annotations

from typing import Any

from bt_api_ib_web.containers.ib._base import _IbContainerBase, _to_float


class IbTradeData(_IbContainerBase):
    def __init__(
        self,
        trade_info: Any,
        symbol_name: Any = None,
        asset_type: Any = "STK",
        has_been_json_encoded: Any = False,
    ) -> None:
        super().__init__(
            "trade_info",
            trade_info,
            symbol_name=symbol_name,
            asset_type=asset_type,
            has_been_json_encoded=has_been_json_encoded,
        )
        self.trade_info = trade_info
        self.exec_id: str | None = None
        self.order_id_val: str | int | None = None
        self.perm_id: str | int | None = None
        self.side: str | None = None
        self.shares = 0.0
        self.price_val = 0.0
        self.cum_qty = 0.0
        self.avg_price_val = 0.0
        self.exec_time: str | None = None
        self.commission_val: float | None = None
        self.exchange_val: str | None = None

    def init_data(self) -> "IbTradeData":
        if self._initialized:
            return self
        info = self.trade_info if isinstance(self.trade_info, dict) else {}
        self.exec_id = str(info.get("execId", ""))
        self.order_id_val = info.get("orderId")
        self.perm_id = info.get("permId")
        self.side = str(info.get("side", "BOT"))
        self.shares = _to_float(info.get("shares"))
        self.price_val = _to_float(info.get("price"))
        self.cum_qty = _to_float(info.get("cumQty"))
        self.avg_price_val = _to_float(info.get("avgPrice"))
        self.exec_time = info.get("time", "")
        self.commission_val = _to_float(info.get("commission"))
        self.exchange_val = str(info.get("exchange", ""))
        self._initialized = True
        return self

    def get_asset_type(self) -> str:
        return str(self.asset_type)

    def get_symbol_name(self) -> str:
        return str(self.symbol_name or "")

    def get_server_time(self) -> str | None:
        return self.exec_time

    def get_trade_id(self) -> str | None:
        return str(self.exec_id) if self.exec_id is not None else None

    def get_order_id(self) -> str | int | None:
        return self.order_id_val

    def get_client_order_id(self) -> str | int | None:
        return self.perm_id

    def get_trade_side(self) -> str:
        return "buy" if self.side == "BOT" else "sell"

    def get_trade_offset(self) -> None:
        return None

    def get_trade_price(self) -> float:
        return self.price_val

    def get_trade_volume(self) -> float:
        return self.shares

    def get_trade_time(self) -> str | None:
        return self.exec_time

    def get_trade_fee(self) -> float:
        return self.commission_val or 0.0

    def get_trade_fee_symbol(self) -> str:
        return "USD"

    def get_all_data(self) -> dict[str, Any]:
        return {
            "exchange_name": self.exchange_name,
            "exec_id": self.exec_id,
            "order_id": self.order_id_val,
            "side": self.side,
            "shares": self.shares,
            "price": self.price_val,
            "cum_qty": self.cum_qty,
            "avg_price": self.avg_price_val,
            "exec_time": self.exec_time,
            "commission": self.commission_val,
            "exchange": self.exchange_val,
        }
