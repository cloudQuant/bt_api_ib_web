from __future__ import annotations

from typing import Any

from bt_api_ib_web.containers.ib._base import _IbContainerBase, _to_float


class IbPositionData(_IbContainerBase):
    def __init__(
        self,
        position_info: Any,
        symbol_name: Any = None,
        asset_type: Any = 'STK',
        has_been_json_encoded: Any = False,
    ) -> None:
        super().__init__(
            'position_info',
            position_info,
            symbol_name=symbol_name,
            asset_type=asset_type,
            has_been_json_encoded=has_been_json_encoded,
        )
        self.position_info = position_info
        self.account: str | None = None
        self.contract_symbol: str | None = None
        self.sec_type: str | None = None
        self.position_val: float | None = None
        self.avg_cost: float | None = None
        self.market_price_val: float | None = None
        self.market_value: float | None = None
        self.unrealized_pnl_val: float | None = None
        self.realized_pnl_val: float | None = None
        self.currency: str | None = None

    def init_data(self) -> IbPositionData:
        if self._initialized:
            return self
        info = self.position_info if isinstance(self.position_info, dict) else {}
        self.account = info.get('account', '')
        self.contract_symbol = info.get('symbol', self.symbol_name)
        self.sec_type = info.get('secType', self.asset_type)
        self.position_val = _to_float(info.get('position'))
        self.avg_cost = _to_float(info.get('avgCost'))
        self.market_price_val = _to_float(info.get('marketPrice'))
        self.market_value = _to_float(info.get('marketValue'))
        self.unrealized_pnl_val = _to_float(info.get('unrealizedPNL'))
        self.realized_pnl_val = _to_float(info.get('realizedPNL'))
        self.currency = str(info.get('currency', 'USD'))
        self._initialized = True
        return self

    def get_asset_type(self) -> str:
        return str(self.sec_type or self.asset_type)

    def get_symbol_name(self) -> str:
        return str(self.contract_symbol or self.symbol_name or '')

    def get_position_volume(self) -> float:
        return self.position_val or 0.0

    def get_avg_price(self) -> float:
        return self.avg_cost or 0.0

    def get_mark_price(self) -> float | None:
        return self.market_price_val

    def get_liquidation_price(self) -> None:
        return None

    def get_initial_margin(self) -> float:
        return 0.0

    def get_maintain_margin(self) -> float:
        return 0.0

    def get_position_unrealized_pnl(self) -> float:
        return self.unrealized_pnl_val or 0.0

    def get_position_funding_value(self) -> float:
        return 0.0

    def get_all_data(self) -> dict[str, Any]:
        return {
            'exchange_name': self.exchange_name,
            'account': self.account,
            'symbol': self.contract_symbol,
            'sec_type': self.sec_type,
            'position': self.position_val,
            'avg_cost': self.avg_cost,
            'market_price': self.market_price_val,
            'market_value': self.market_value,
            'unrealized_pnl': self.unrealized_pnl_val,
            'realized_pnl': self.realized_pnl_val,
            'currency': self.currency,
        }
