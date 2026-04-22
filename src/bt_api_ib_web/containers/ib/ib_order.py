from __future__ import annotations

from typing import Any

from bt_api_base.containers.orders.order import OrderStatus

from bt_api_ib_web.containers.ib._base import _IbContainerBase, _to_float

IB_ORDER_STATUS_MAP = {
    "PendingSubmit": OrderStatus.SUBMITTED,
    "PendingCancel": OrderStatus.SUBMITTED,
    "PreSubmitted": OrderStatus.SUBMITTED,
    "Submitted": OrderStatus.ACCEPTED,
    "ApiPending": OrderStatus.SUBMITTED,
    "ApiCancelled": OrderStatus.CANCELED,
    "Cancelled": OrderStatus.CANCELED,
    "Filled": OrderStatus.COMPLETED,
    "Inactive": OrderStatus.REJECTED,
}


class IbOrderData(_IbContainerBase):
    def __init__(
        self,
        order_info: Any,
        symbol_name: Any = None,
        asset_type: Any = "STK",
        has_been_json_encoded: Any = False,
    ) -> None:
        super().__init__(
            "order_info",
            order_info,
            symbol_name=symbol_name,
            asset_type=asset_type,
            has_been_json_encoded=has_been_json_encoded,
        )
        self.order_info = order_info
        self.order_id_val: int | str | None = None
        self.perm_id: int | str | None = None
        self.client_id: int | str | None = None
        self.action: str | None = None
        self.total_quantity = 0.0
        self.order_type_val: str | None = None
        self.lmt_price = 0.0
        self.aux_price = 0.0
        self.tif: str | None = None
        self.oca_group: str | None = None
        self.status_val: OrderStatus | None = None
        self.filled = 0.0
        self.remaining = 0.0
        self.avg_fill_price = 0.0
        self.last_fill_time: str | None = None

    def init_data(self) -> IbOrderData:
        if self._initialized:
            return self
        info = self.order_info if isinstance(self.order_info, dict) else {}
        self.order_id_val = info.get("orderId")
        self.perm_id = info.get("permId")
        self.client_id = info.get("clientId")
        self.action = str(info.get("action", "BUY"))
        self.total_quantity = _to_float(info.get("totalQuantity"))
        self.order_type_val = str(info.get("orderType", "LMT"))
        self.lmt_price = _to_float(info.get("lmtPrice"))
        self.aux_price = _to_float(info.get("auxPrice"))
        self.tif = str(info.get("tif", "DAY"))
        self.oca_group = str(info.get("ocaGroup", ""))
        status_str = str(info.get("status", "PendingSubmit"))
        self.status_val = IB_ORDER_STATUS_MAP.get(status_str, OrderStatus.SUBMITTED)
        self.filled = _to_float(info.get("filled"))
        self.remaining = _to_float(info.get("remaining"))
        self.avg_fill_price = _to_float(info.get("avgFillPrice"))
        self.last_fill_time = info.get("lastFillTime")
        self._initialized = True
        return self

    def get_asset_type(self) -> str:
        return str(self.asset_type)

    def get_symbol_name(self) -> str:
        return str(self.symbol_name or "")

    def get_server_time(self) -> str | None:
        return self.last_fill_time

    def get_local_update_time(self) -> str | None:
        return self.last_fill_time

    def get_order_id(self) -> int | str | None:
        return self.order_id_val

    def get_client_order_id(self) -> int | str | None:
        return self.perm_id

    def get_order_size(self) -> float:
        return self.total_quantity

    def get_order_price(self) -> float:
        return self.lmt_price

    def get_order_side(self) -> str | None:
        return self.action.lower() if self.action else None

    def get_order_status(self) -> OrderStatus | None:
        return self.status_val

    def get_executed_qty(self) -> float:
        return self.filled

    def get_order_symbol_name(self) -> str:
        return str(self.symbol_name or "")

    def get_order_type(self) -> str | None:
        return self.order_type_val

    def get_order_avg_price(self) -> float:
        return self.avg_fill_price

    def get_order_time_in_force(self) -> str | None:
        return self.tif

    def get_order_exchange_id(self) -> str:
        return "SMART"

    def __str__(self) -> str:
        return (
            f"IbOrder({self.symbol_name}, {self.action}, type={self.order_type_val}, "
            f"price={self.lmt_price}, qty={self.total_quantity}, status={self.status_val})"
        )

    def __repr__(self) -> str:
        return str(self)
