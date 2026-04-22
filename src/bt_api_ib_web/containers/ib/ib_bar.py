from __future__ import annotations

from typing import Any

from bt_api_ib_web.containers.ib._base import _IbContainerBase, _to_float, _to_int


class IbBarData(_IbContainerBase):
    def __init__(
        self,
        bar_info: Any,
        symbol_name: Any = None,
        asset_type: Any = 'STK',
        has_been_json_encoded: Any = False,
    ) -> None:
        super().__init__(
            'bar_info',
            bar_info,
            symbol_name=symbol_name,
            asset_type=asset_type,
            has_been_json_encoded=has_been_json_encoded,
        )
        self.bar_info = bar_info
        self.date_val: str | None = None
        self.open_val = 0.0
        self.high_val = 0.0
        self.low_val = 0.0
        self.close_val = 0.0
        self.volume_val = 0
        self.wap_val = 0.0
        self.bar_count = 0

    def init_data(self) -> IbBarData:
        if self._initialized:
            return self
        info = self.bar_info if isinstance(self.bar_info, dict) else {}
        self.date_val = info.get('date', '')
        self.open_val = _to_float(info.get('open'))
        self.high_val = _to_float(info.get('high'))
        self.low_val = _to_float(info.get('low'))
        self.close_val = _to_float(info.get('close'))
        self.volume_val = _to_int(info.get('volume'))
        self.wap_val = _to_float(info.get('wap'))
        self.bar_count = _to_int(info.get('barCount'))
        self._initialized = True
        return self

    def get_symbol_name(self) -> str:
        return str(self.symbol_name or '')

    def get_asset_type(self) -> str:
        return str(self.asset_type)

    def get_server_time(self) -> str | None:
        return self.date_val

    def get_open_time(self) -> str | None:
        return self.date_val

    def get_open_price(self) -> float:
        return self.open_val

    def get_high_price(self) -> float:
        return self.high_val

    def get_low_price(self) -> float:
        return self.low_val

    def get_close_price(self) -> float:
        return self.close_val

    def get_volume(self) -> int:
        return self.volume_val

    def get_amount(self) -> None:
        return None

    def get_close_time(self) -> str | None:
        return self.date_val

    def get_bar_status(self) -> bool:
        return True

    def get_num_trades(self) -> int:
        return self.bar_count

    def get_wap(self) -> float:
        return self.wap_val

    def get_all_data(self) -> dict[str, Any]:
        return {
            'exchange_name': self.exchange_name,
            'symbol_name': self.symbol_name,
            'date': self.date_val,
            'open': self.open_val,
            'high': self.high_val,
            'low': self.low_val,
            'close': self.close_val,
            'volume': self.volume_val,
            'wap': self.wap_val,
            'bar_count': self.bar_count,
        }
