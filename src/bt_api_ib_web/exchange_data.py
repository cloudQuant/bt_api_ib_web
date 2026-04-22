from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from bt_api_base.config_loader import ExchangeConfig, load_exchange_config
from bt_api_base.containers.exchanges.exchange_data import ExchangeData

try:
    import yaml
except ImportError:
    yaml = None

__all__ = [
    "IbWebExchangeData",
    "IbWebExchangeDataForex",
    "IbWebExchangeDataFuture",
    "IbWebExchangeDataOption",
    "IbWebExchangeDataStock",
    "_get_ib_config",
    "_get_ib_raw_config",
    "_get_ib_yaml_path",
]


def _get_ib_yaml_path() -> str:
    return str(Path(__file__).resolve().parent / "configs" / "ib.yaml")


@lru_cache(maxsize=1)
def _get_ib_raw_config() -> dict[str, Any]:
    if yaml is None:
        raise ImportError("PyYAML is required to load ib.yaml")
    with Path(_get_ib_yaml_path()).open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _get_ib_config() -> ExchangeConfig:
    return load_exchange_config(_get_ib_yaml_path())


class IbWebExchangeData(ExchangeData):
    PROD_REST_URL = "https://api.interactivebrokers.com"
    TEST_REST_URL = "https://api.test.interactivebrokers.com"
    GATEWAY_REST_URL = "https://localhost:5000"

    def __init__(self, asset_type: str = "stk") -> None:
        super().__init__()
        config = _get_ib_config()
        raw = _get_ib_raw_config()
        asset_key = str(asset_type or "stk").strip().lower()
        asset_config = config.asset_types[asset_key]
        base_urls = config.base_urls

        self.exchange_name = str(asset_config.exchange_name or "")
        self.rest_url = str(
            asset_config.rest_url or (base_urls.rest.get("default", "") if base_urls else "")
        )
        self.wss_url = str(
            asset_config.wss_url or (base_urls.wss.get("default", "") if base_urls else "")
        )
        self.acct_wss_url = str(
            base_urls.acct_wss.get("default", self.wss_url) if base_urls else self.wss_url
        )
        self.symbol_format = asset_config.symbol_format
        self.rest_paths = dict(asset_config.rest_paths)
        self.wss_paths = dict(asset_config.wss_paths)
        self.kline_periods = dict(config.kline_periods or {})
        self.reverse_kline_periods = {value: key for key, value in self.kline_periods.items()}
        self.status_dict = dict(config.status_dict or {})
        self.sec_type_map = {
            str(key): str(value) for key, value in (raw.get("sec_type_map") or {}).items()
        }
        self.market_data_fields = {
            str(key): str(value) for key, value in (raw.get("market_data_fields") or {}).items()
        }
        self.default_snapshot_fields = [
            str(value) for value in (raw.get("default_snapshot_fields") or [])
        ]
        self.order_type_map = {
            str(key): str(value) for key, value in (raw.get("order_type_map") or {}).items()
        }
        self.tif_map = {str(key): str(value) for key, value in (raw.get("tif_map") or {}).items()}
        self.rate_limits_config = {
            str(rule.name): rule.limit / rule.interval for rule in config.rate_limits
        }

    def get_period(self, period: str) -> str:
        return self.kline_periods.get(period, period)

    def get_symbol(self, symbol: str) -> str:
        return str(symbol)

    def get_snapshot_fields_str(self, fields: list[str] | None = None) -> str:
        values = [str(item) for item in (fields or self.default_snapshot_fields)]
        return ",".join(values)

    def get_rest_path(self, key: str) -> str:
        path = self.rest_paths.get(key)
        if not path:
            self.raise_path_error(self.exchange_name or "IB_WEB", key)
        return str(path)

    def get_rest_url(self, key: str, **params: Any) -> tuple[str, str]:
        template = self.get_rest_path(key)
        method, raw_path = template.split(" ", 1)
        return method, f"{self.rest_url}{raw_path.format(**params)}"

    def get_wss_path(self) -> str:
        return self.wss_url


class IbWebExchangeDataStock(IbWebExchangeData):
    def __init__(self) -> None:
        super().__init__("stk")


class IbWebExchangeDataFuture(IbWebExchangeData):
    def __init__(self) -> None:
        super().__init__("fut")


class IbWebExchangeDataOption(IbWebExchangeData):
    def __init__(self) -> None:
        super().__init__("opt")


class IbWebExchangeDataForex(IbWebExchangeData):
    def __init__(self) -> None:
        super().__init__("cash")
