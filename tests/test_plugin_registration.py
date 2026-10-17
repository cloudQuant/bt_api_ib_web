from __future__ import annotations

from bt_api_base.balance_utils import simple_balance_handler
from bt_api_ib_web.exchange_data import IbWebExchangeDataFuture, IbWebExchangeDataStock
from bt_api_ib_web.plugin import register_plugin
from bt_api_ib_web.runtime.feed import IbWebRequestDataFuture, IbWebRequestDataStock


class _RecordingRegistry:
    registrations: list[tuple[str, str, object]] = []

    @classmethod
    def register_feed(cls, exchange: str, feed: object) -> None:
        cls.registrations.append(("feed", exchange, feed))

    @classmethod
    def register_exchange_data(cls, exchange: str, exchange_data: object) -> None:
        cls.registrations.append(("exchange_data", exchange, exchange_data))

    @classmethod
    def register_balance_handler(cls, exchange: str, handler: object) -> None:
        cls.registrations.append(("balance_handler", exchange, handler))


def test_plugin_registers_direct_stock_and_future_feeds() -> None:
    _RecordingRegistry.registrations = []

    info = register_plugin(_RecordingRegistry)

    assert info.supported_exchanges == ("IB_WEB___STK", "IB_WEB___FUT")
    assert info.supported_asset_types == ("STK", "FUT")
    assert _RecordingRegistry.registrations == [
        ("feed", "IB_WEB___STK", IbWebRequestDataStock),
        ("exchange_data", "IB_WEB___STK", IbWebExchangeDataStock),
        ("balance_handler", "IB_WEB___STK", simple_balance_handler),
        ("feed", "IB_WEB___FUT", IbWebRequestDataFuture),
        ("exchange_data", "IB_WEB___FUT", IbWebExchangeDataFuture),
        ("balance_handler", "IB_WEB___FUT", simple_balance_handler),
    ]
