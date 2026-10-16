"""Module-level docstring."""
from __future__ import annotations

from typing import Any

from bt_api_ib_web.containers.ib._base import _IbContainerBase, _to_float


class IbAccountData(_IbContainerBase):
    """Class IbAccountData"""
    def __init__(
        self,
        account_info: Any,
        symbol_name: Any = None,
        asset_type: Any = 'STK',
        has_been_json_encoded: Any = False,
    ) -> None:
        """__init__ method"""
        super().__init__(
            'account_info',
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
        self.initial_margin: float | None = None
        self.maintenance_margin: float | None = None
        self.available_funds: float | None = None
        self.unrealized_pnl: float | None = None
        self.realized_pnl: float | None = None
        self.currency: str | None = None

    def init_data(self) -> IbAccountData:
        """init_data method"""
        if self._initialized:
            return self
        info = self.account_info if isinstance(self.account_info, dict) else {}
        self.account_id = info.get('AccountID', info.get('account', ''))
        self.net_liquidation = _to_float(
            _first_value(
                info, 'NetLiquidation', 'net_liquidation', 'netliquidation', 'value'
            )
        )
        self.total_cash_value = _to_float(
            _first_value(
                info,
                'TotalCashValue',
                'total_cash_value',
                'CashBalance',
                'cashbalance',
                'balance',
            )
        )
        self.buying_power = _to_float(
            _first_value(info, 'BuyingPower', 'buying_power', 'buyingpower')
        )
        self.gross_position_value = _to_float(
            _first_value(info, 'GrossPositionValue', 'gross_position_value')
        )
        self.initial_margin = _to_float(
            _first_value(info, 'InitMarginReq', 'initial_margin', 'init_margin')
        )
        self.maintenance_margin = _to_float(
            _first_value(info, 'MaintMarginReq', 'maintenance_margin', 'maint_margin')
        )
        self.available_funds = _to_float(
            _first_value(
                info, 'AvailableFunds', 'available_funds', 'availablefunds', 'cash'
            )
        )
        self.unrealized_pnl = _to_float(
            _first_value(info, 'UnrealizedPnL', 'unrealized_pnl', 'unrealizedpnl')
        )
        self.realized_pnl = _to_float(
            _first_value(info, 'RealizedPnL', 'realized_pnl', 'realizedpnl')
        )
        self.currency = str(info.get('Currency', 'USD'))
        self._initialized = True
        return self

    def get_asset_type(self) -> str:
        """get_asset_type method"""
        return str(self.asset_type)

    def get_account_type(self) -> str:
        """get_account_type method"""
        return str(self.currency or 'USD')

    def get_server_time(self) -> float:
        """get_server_time method"""
        return 0.0

    def get_total_wallet_balance(self) -> float:
        """get_total_wallet_balance method"""
        return self.net_liquidation or 0.0

    def get_margin(self) -> float:
        """get_margin method"""
        return (self.net_liquidation or 0.0) - (self.unrealized_pnl or 0.0)

    def get_available_margin(self) -> float:
        """get_available_margin method"""
        return self.available_funds or 0.0

    def get_unrealized_profit(self) -> float:
        """get_unrealized_profit method"""
        return self.unrealized_pnl or 0.0

    def get_balances(self) -> list[IbAccountData]:
        """get_balances method"""
        return [self]

    def get_positions(self) -> list[Any]:
        """get_positions method"""
        return []

    def get_all_data(self) -> dict[str, Any]:
        """get_all_data method"""
        return {
            'exchange_name': self.exchange_name,
            'account_id': self.account_id,
            'net_liquidation': self.net_liquidation,
            'total_cash_value': self.total_cash_value,
            'buying_power': self.buying_power,
            'available_funds': self.available_funds,
            'initial_margin': self.initial_margin,
            'maintenance_margin': self.maintenance_margin,
            'gross_position_value': self.gross_position_value,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'currency': self.currency,
        }

    def get_balance_projection(self) -> dict[str, Any]:
        """Return the direct balance fields in a flat, consumer-friendly shape."""
        self.init_data()
        info = self.account_info if isinstance(self.account_info, dict) else {}
        available = _first_float(
            info,
            ('available', 'available_funds', 'availablefunds', 'AvailableFunds', 'cash'),
        )
        cash_balance = _first_float(
            info,
            ('balance', 'CashBalance', 'cashbalance', 'TotalCashValue', 'totalcashvalue'),
        )
        value = _first_float(
            info,
            ('value', 'equity', 'NetLiquidation', 'netliquidation', 'EquityWithLoanValue'),
        )
        used_margin = _first_float(
            info,
            ('margin', 'used_margin', 'InitMarginReq', 'initmarginreq', 'MaintMarginReq'),
        )
        buying_power = _first_float(info, ('buying_power', 'buyingpower', 'BuyingPower'))
        unrealized_pnl = _first_float(
            info, ('unrealized_pnl', 'UnrealizedPnL', 'unrealizedpnl')
        )
        if available is None and value is not None and used_margin is not None:
            available = value - used_margin
        if available is None:
            available = cash_balance if cash_balance is not None else 0.0
        if cash_balance is None:
            cash_balance = available
        if value is None:
            value = cash_balance

        projection = dict(info)
        projection.update(
            {
                'cash': available,
                'available': available,
                'available_funds': available,
                'balance': cash_balance,
                'value': value,
                'equity': value,
            }
        )
        if used_margin is not None:
            projection.setdefault('margin', used_margin)
            projection.setdefault('used_margin', used_margin)
        if buying_power is not None:
            projection.setdefault('buying_power', buying_power)
        if unrealized_pnl is not None:
            projection.setdefault('unrealized_pnl', unrealized_pnl)
        return projection


def _first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _first_float(payload: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key not in payload:
            continue
        value = _optional_float(payload[key])
        if value is not None:
            return value
    return None


def _optional_float(value: Any) -> float | None:
    if isinstance(value, dict):
        for key in ('amount', 'value', 'balance', 'total'):
            if key in value:
                return _optional_float(value[key])
    if value is None or value == '' or isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.strip().replace(',', '')
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
