from __future__ import annotations

from typing import Any

from bt_api_base.gateway.registrar import GatewayRuntimeRegistrar
from bt_api_base.plugins.protocol import PluginInfo
from bt_api_base.registry import ExchangeRegistry

from bt_api_ib_web import __version__
from bt_api_ib_web.gateway.adapter import IbWebGatewayAdapter


def register_plugin(
    registry: type[ExchangeRegistry], runtime_factory: type[GatewayRuntimeRegistrar]
) -> PluginInfo:
    # Direct registration to isolated registry instead of calling legacy register_ib_web()
    from bt_api_py.balance_utils import simple_balance_handler as _ib_web_balance_handler
    from bt_api_py.containers.exchanges.ib_web_exchange_data import (
        IbWebExchangeDataFuture,
        IbWebExchangeDataStock,
    )
    from bt_api_py.feeds.live_ib_web_feed import IbWebRequestDataFuture, IbWebRequestDataStock

    # Stock
    registry.register_feed("IB_WEB___STK", IbWebRequestDataStock)
    registry.register_exchange_data("IB_WEB___STK", IbWebExchangeDataStock)
    registry.register_balance_handler("IB_WEB___STK", _ib_web_balance_handler)

    # Future
    registry.register_feed("IB_WEB___FUT", IbWebRequestDataFuture)
    registry.register_exchange_data("IB_WEB___FUT", IbWebExchangeDataFuture)
    registry.register_balance_handler("IB_WEB___FUT", _ib_web_balance_handler)

    runtime_factory.register_adapter("IB_WEB", IbWebGatewayAdapter)

    return PluginInfo(
        name="bt_api_ib_web",
        version=__version__,
        core_requires=">=0.15,<1.0",
        supported_exchanges=("IB_WEB___STK", "IB_WEB___FUT"),
        supported_asset_types=("STK", "FUT"),
    )
