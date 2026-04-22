from __future__ import annotations

from typing import Any

from bt_api_ib_web.containers.ib._base import _IbContainerBase, _to_float


class IbAccountData(_IbContainerBase):
    def __init__(
        self,
        account_info: Any,
        symbol_name: Any = None,
        asset_type: Any = "STK",
        has_been_json_encoded: Any = False,
    ) -> None:
        super().__init__(
            "account_info",
            account_info,
            symbol_name=symbol_name,
            asset_type=asset_type,
            has_been_json_encoded=has_been_json_encoded,
        )
        self.account_info = account_info
        self.account_id: str | None = None
        self.net_liquidation: float | None = None
        self.total_cash_value: float | None = None
        self.buying_power: float | None = None
        self.gross_position_value: float | None = None
        self.maintenance_margin: float | None = None
        self.available_funds: float | None = None
        self.unrealized_pnl: float | None = None
        self.realized_pnl: float | None = None
        self.currency: str | None = None

    def init_data(self) -> IbAccountData:
        if self._initialized:
            return self
        info = self.account_info if isinstance(self.account_info, dict) else {}
        self.account_id = info.get("AccountID", info.get("account", ""))
        self.net_liquidation = _to_float(info.get("NetLiquidation"))
        self.total_cash_value = _to_float(info.get("TotalCashValue"))
        self.buying_power = _to_float(info.get("BuyingPower"))
        self.gross_position_value = _to_float(info.get("GrossPositionValue"))
        self.maintenance_margin = _to_float(info.get("MaintMarginReq"))
        self.available_funds = _to_float(info.get("AvailableFunds"))
        self.unrealized_pnl = _to_float(info.get("UnrealizedPnL"))
        self.realized_pnl = _to_float(info.get("RealizedPnL"))
        self.currency = str(info.get("Currency", "USD"))
        self._initialized = True
        return self

    def get_asset_type(self) -> str:
        return str(self.asset_type)

    def get_account_type(self) -> str:
        return str(self.currency or "USD")

    def get_server_time(self) -> float:
        return 0.0

    def get_total_wallet_balance(self) -> float:
        return self.net_liquidation or 0.0

    def get_margin(self) -> float:
        return self.net_liquidation or 0.0

    def get_available_margin(self) -> float:
        return self.available_funds or 0.0

    def get_unrealized_profit(self) -> float:
        return self.unrealized_pnl or 0.0

    def get_balances(self) -> list[IbAccountData]:
        return [self]

    def get_positions(self) -> list[Any]:
        return []

    def get_all_data(self) -> dict[str, Any]:
        return {
            "exchange_name": self.exchange_name,
            "account_id": self.account_id,
            "net_liquidation": self.net_liquidation,
            "total_cash_value": self.total_cash_value,
            "buying_power": self.buying_power,
            "available_funds": self.available_funds,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "currency": self.currency,
        }
