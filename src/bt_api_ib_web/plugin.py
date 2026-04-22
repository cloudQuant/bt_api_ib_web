from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bt_api_base.gateway.registrar import GatewayRuntimeRegistrar
    from bt_api_base.registry import ExchangeRegistry

from bt_api_base.balance_utils import simple_balance_handler as _ib_web_balance_handler
from bt_api_base.plugins.protocol import PluginInfo

from bt_api_ib_web import __version__
from bt_api_ib_web.exchange_data import IbWebExchangeDataFuture, IbWebExchangeDataStock
from bt_api_ib_web.gateway.adapter import IbWebGatewayAdapter
from bt_api_ib_web.runtime.feed import IbWebRequestDataFuture, IbWebRequestDataStock


def register_plugin(
    registry: type[ExchangeRegistry], runtime_factory: type[GatewayRuntimeRegistrar]
) -> PluginInfo:
    registry.register_feed("IB_WEB___STK", IbWebRequestDataStock)
    registry.register_exchange_data("IB_WEB___STK", IbWebExchangeDataStock)
    registry.register_balance_handler("IB_WEB___STK", _ib_web_balance_handler)

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
