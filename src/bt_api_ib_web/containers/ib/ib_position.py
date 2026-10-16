"""Module-level docstring."""
from __future__ import annotations

from typing import Any

from bt_api_ib_web.containers.ib._base import _IbContainerBase, _to_float


class IbPositionData(_IbContainerBase):
    """Class IbPositionData"""
    def __init__(
        self,
        position_info: Any,
        symbol_name: Any = None,
        asset_type: Any = 'STK',
        has_been_json_encoded: Any = False,
    ) -> None:
        """__init__ method"""
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
        """init_data method"""
        if self._initialized:
            return self
        info = self.position_info if isinstance(self.position_info, dict) else {}
        self.account = _first_text(info, ('account', 'acctId', 'AccountID'))
        self.contract_symbol = _first_text(
            info,
            (
                'data_name',
                'symbol',
                'localSymbol',
                'local_symbol',
                'contractDesc',
                'contract_desc',
                'description',
                'ticker',
                'conid',
            ),
        ) or self.symbol_name
        self.sec_type = _first_text(
            info, ('sec_type', 'secType', 'asset_type', 'assetClass')
        ) or self.asset_type
        self.position_val = _to_float(
            _first_value(info, 'size', 'volume', 'position', 'qty', 'quantity')
        )
        self.avg_cost = _to_float(
            _first_value(
                info,
                'price',
                'avg_price',
                'average_price',
                'avgCost',
                'avgPrice',
                'averageCost',
            )
        )
        self.market_price_val = _to_float(
            _first_value(
                info,
                'current_price',
                'latest_price',
                'last_price',
                'marketPrice',
                'mktPrice',
                'markPrice',
                'market_price',
            )
        )
        self.market_value = _to_float(
            _first_value(info, 'market_value', 'marketValue', 'mktValue', 'value')
        )
        self.unrealized_pnl_val = _to_float(
            _first_value(
                info,
                'unrealized_pnl',
                'unrealizedPNL',
                'UnrealizedPnL',
                'unrealizedPnl',
                'unrealizedpnl',
            )
        )
        self.realized_pnl_val = _to_float(
            _first_value(
                info,
                'realized_pnl',
                'realizedPNL',
                'RealizedPnL',
                'realizedPnl',
                'realizedpnl',
            )
        )
        self.currency = str(_first_value(info, 'currency', 'Currency') or 'USD')
        self._initialized = True
        return self

    def get_asset_type(self) -> str:
        """get_asset_type method"""
        return str(self.sec_type or self.asset_type)

    def get_symbol_name(self) -> str:
        """get_symbol_name method"""
        return str(self.contract_symbol or self.symbol_name or '')

    def get_position_volume(self) -> float:
        """get_position_volume method"""
        return self.position_val or 0.0

    def get_avg_price(self) -> float:
        """get_avg_price method"""
        return self.avg_cost or 0.0

    def get_mark_price(self) -> float | None:
        """get_mark_price method"""
        return self.market_price_val

    def get_liquidation_price(self) -> None:
        """get_liquidation_price method"""
        return None

    def get_initial_margin(self) -> float:
        """get_initial_margin method"""
        return 0.0

    def get_maintain_margin(self) -> float:
        """get_maintain_margin method"""
        return 0.0

    def get_position_unrealized_pnl(self) -> float:
        """get_position_unrealized_pnl method"""
        return self.unrealized_pnl_val or 0.0

    def get_position_funding_value(self) -> float:
        """get_position_funding_value method"""
        return 0.0

    def get_all_data(self) -> dict[str, Any]:
        """get_all_data method"""
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

    def get_position_projection(self) -> dict[str, Any]:
        """Return the native position in a flat, consumer-friendly shape."""
        self.init_data()
        payload = dict(self.position_info) if isinstance(self.position_info, dict) else {}
        symbol = str(self.contract_symbol or self.symbol_name or '')
        size = self.position_val or 0.0
        entry_price = self.avg_cost or 0.0
        current_price = self.market_price_val
        sec_type = str(self.sec_type or self.asset_type or '')
        payload.update(
            {
                'account': self.account,
                'symbol': symbol,
                'instrument': symbol,
                'data_name': symbol,
                'size': size,
                'volume': abs(size),
                'price': entry_price,
                'avg_price': entry_price,
                'direction': 'short' if size < 0 else 'long',
                'asset_type': sec_type,
                'sec_type': sec_type,
            }
        )
        if current_price is not None:
            payload['current_price'] = current_price
            payload['latest_price'] = current_price
            payload['last_price'] = current_price
        if self.market_value is not None:
            payload['market_value'] = self.market_value
        if self.unrealized_pnl_val is not None:
            payload['unrealized_pnl'] = self.unrealized_pnl_val
            payload['gross_pnl'] = self.unrealized_pnl_val
        if self.realized_pnl_val is not None:
            payload['realized_pnl'] = self.realized_pnl_val
        return payload


def _first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value is not None and value != '':
            return value
    return None


def _first_text(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    value = _first_value(payload, *keys)
    return str(value or '').strip()
