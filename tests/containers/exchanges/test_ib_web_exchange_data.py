"""
Tests for IB Web API Exchange Data
 IB Web API

 ib.yaml , Python .
"""

from __future__ import annotations

import os
from importlib import import_module

import pytest
import yaml

_exchange_data_module = import_module("bt_api_ib_web.exchange_data")
IbWebExchangeData = _exchange_data_module.IbWebExchangeData
IbWebExchangeDataForex = _exchange_data_module.IbWebExchangeDataForex
IbWebExchangeDataFuture = _exchange_data_module.IbWebExchangeDataFuture
IbWebExchangeDataOption = _exchange_data_module.IbWebExchangeDataOption
IbWebExchangeDataStock = _exchange_data_module.IbWebExchangeDataStock
_get_ib_config = _exchange_data_module._get_ib_config
_get_ib_raw_config = _exchange_data_module._get_ib_raw_config
_get_ib_yaml_path = _exchange_data_module._get_ib_yaml_path


# ─── helper:  yaml  ─────────────────────────
@pytest.fixture(scope="module")
def yaml_data():
    """ ib.yaml """
    path = _get_ib_yaml_path()
    assert os.path.exists(path), f"ib.yaml not found at {path}"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ═══════════════════════════════════════════════════════════════
# 1. YAML  (pydantic ExchangeConfig)
# ═══════════════════════════════════════════════════════════════


class TestYamlConfigLoading:
    """ ib.yaml  pydantic """

    def test_config_loaded_successfully(self):
        """test_config_loaded_successfully method"""
        config = _get_ib_config()
        assert config is not None, "ib.yaml config should load successfully"

    def test_config_id(self):
        """test_config_id method"""
        assert _get_ib_config().id == "ib_web"

    def test_config_display_name(self):
        """test_config_display_name method"""
        assert "Interactive Brokers" in _get_ib_config().display_name

    def test_config_venue_type(self):
        """test_config_venue_type method"""
        assert _get_ib_config().venue_type.value == "broker"

    def test_config_base_urls_rest(self):
        """test_config_base_urls_rest method"""
        urls = _get_ib_config().base_urls
        assert urls is not None
        assert urls.rest["production"] == "https://api.interactivebrokers.com"
        assert urls.rest["testing"] == "https://api.test.interactivebrokers.com"
        assert urls.rest["gateway"] == "https://localhost:5000"
        assert urls.rest["default"] == "https://localhost:5000"

    def test_config_base_urls_wss(self):
        """test_config_base_urls_wss method"""
        urls = _get_ib_config().base_urls
        assert urls is not None
        assert urls.wss is not None
        assert urls.wss["default"] == "wss://localhost:5000/v1/api/ws"

    def test_config_connection(self):
        """test_config_connection method"""
        conn = _get_ib_config().connection
        assert conn.type.value == "http"
        assert conn.timeout == 10
        assert conn.max_retries == 3

    def test_config_authentication(self):
        """test_config_authentication method"""
        auth = _get_ib_config().authentication
        assert auth is not None
        assert auth.type.value == "oauth"

    @pytest.mark.kline
    def test_config_kline_periods(self):
        """test_config_kline_periods method"""
        kp = _get_ib_config().kline_periods
        assert kp is not None
        assert kp["1m"] == "1min"
        assert kp["1h"] == "1h"
        assert kp["1d"] == "1d"
        assert kp["1M"] == "1m"

    def test_config_status_dict(self):
        """test_config_status_dict method"""
        sd = _get_ib_config().status_dict
        assert sd is not None
        assert sd["submitted"] == "submit"
        assert sd["filled"] == "filled"
        assert sd["cancelled"] == "cancel"
        assert sd["inactive"] == "inactive"
        assert sd["presubmitted"] == "presubmit"

    def test_config_rate_limits_count(self):
        """test_config_rate_limits_count method"""
        assert len(_get_ib_config().rate_limits) >= 5

    def test_config_rate_limit_names(self):
        """test_config_rate_limit_names method"""
        names = {r.name for r in _get_ib_config().rate_limits}
        for expected in (
            "global_trading",
            "cp_gateway",
            "account_management",
            "market_snapshot",
            "orders_query",
        ):
            assert expected in names

    def test_config_asset_types_keys(self):
        """test_config_asset_types_keys method"""
        at = _get_ib_config().asset_types
        for key in ("stk", "fut", "opt", "cash"):
            assert key in at

    def test_config_asset_type_stk_name(self):
        """test_config_asset_type_stk_name method"""
        assert _get_ib_config().asset_types["stk"].exchange_name == "IB_WEB_STK"

    def test_config_asset_type_fut_name(self):
        """test_config_asset_type_fut_name method"""
        assert _get_ib_config().asset_types["fut"].exchange_name == "IB_WEB_FUT"

    def test_config_asset_type_opt_name(self):
        """test_config_asset_type_opt_name method"""
        assert _get_ib_config().asset_types["opt"].exchange_name == "IB_WEB_OPT"

    def test_config_asset_type_cash_name(self):
        """test_config_asset_type_cash_name method"""
        assert _get_ib_config().asset_types["cash"].exchange_name == "IB_WEB_CASH"

    def test_config_yaml_anchor_shared_paths(self):
        """YAML :  asset_type  rest_paths"""
        at = _get_ib_config().asset_types
        stk_paths = at["stk"].rest_paths
        for key in ("fut", "opt", "cash"):
            assert at[key].rest_paths == stk_paths, f"{key} rest_paths differs from stk"


# ═══════════════════════════════════════════════════════════════
# 2.  YAML dict  (pydantic )
# ═══════════════════════════════════════════════════════════════


class TestRawYamlConfig:
    """ _get_ib_raw_config  yaml dict ( pydantic )"""

    def test_raw_config_loaded(self):
        """test_raw_config_loaded method"""
        raw = _get_ib_raw_config()
        assert raw is not None
        assert isinstance(raw, dict)

    def test_raw_has_sec_type_map(self):
        """test_raw_has_sec_type_map method"""
        raw = _get_ib_raw_config()
        assert "sec_type_map" in raw
        assert raw["sec_type_map"]["STK"] == "Stock"
        assert raw["sec_type_map"]["FUT"] == "Future"

    def test_raw_has_market_data_fields(self):
        """test_raw_has_market_data_fields method"""
        raw = _get_ib_raw_config()
        assert "market_data_fields" in raw
        assert str(raw["market_data_fields"]["last_price"]) == "31"
        assert str(raw["market_data_fields"]["bid_price"]) == "84"

    def test_raw_has_default_snapshot_fields(self):
        """test_raw_has_default_snapshot_fields method"""
        raw = _get_ib_raw_config()
        assert "default_snapshot_fields" in raw
        assert "31" in [str(f) for f in raw["default_snapshot_fields"]]

    def test_raw_has_order_type_map(self):
        """test_raw_has_order_type_map method"""
        raw = _get_ib_raw_config()
        assert "order_type_map" in raw
        assert raw["order_type_map"]["market"] == "MKT"
        assert raw["order_type_map"]["limit"] == "LMT"

    def test_raw_has_tif_map(self):
        """test_raw_has_tif_map method"""
        raw = _get_ib_raw_config()
        assert "tif_map" in raw
        assert raw["tif_map"]["day"] == "DAY"
        assert raw["tif_map"]["gtc"] == "GTC"


# ═══════════════════════════════════════════════════════════════
# 3. Python  == YAML  ()
# ═══════════════════════════════════════════════════════════════


class TestAllFieldsFromYaml:
    """: Python  == ib.yaml """

    @pytest.fixture
    def stk(self):
        """stk method"""
        return IbWebExchangeDataStock()

    @pytest.mark.kline
    def test_kline_periods_match_yaml(self, stk, yaml_data):
        """test_kline_periods_match_yaml method"""
        for k, v in yaml_data["kline_periods"].items():
            assert stk.kline_periods[k] == v, f"kline_periods[{k}] mismatch"

    def test_status_dict_match_yaml(self, stk, yaml_data):
        """test_status_dict_match_yaml method"""
        for k, v in yaml_data["status_dict"].items():
            assert stk.status_dict[k] == v, f"status_dict[{k}] mismatch"

    def test_sec_type_map_match_yaml(self, stk, yaml_data):
        """test_sec_type_map_match_yaml method"""
        for k, v in yaml_data["sec_type_map"].items():
            assert stk.sec_type_map[k] == v, f"sec_type_map[{k}] mismatch"

    def test_market_data_fields_match_yaml(self, stk, yaml_data):
        """test_market_data_fields_match_yaml method"""
        for k, v in yaml_data["market_data_fields"].items():
            assert stk.market_data_fields[k] == str(v), f"market_data_fields[{k}] mismatch"

    def test_default_snapshot_fields_match_yaml(self, stk, yaml_data):
        """test_default_snapshot_fields_match_yaml method"""
        expected = [str(f) for f in yaml_data["default_snapshot_fields"]]
        assert stk.default_snapshot_fields == expected

    def test_order_type_map_match_yaml(self, stk, yaml_data):
        """test_order_type_map_match_yaml method"""
        for k, v in yaml_data["order_type_map"].items():
            assert stk.order_type_map[k] == v, f"order_type_map[{k}] mismatch"

    def test_tif_map_match_yaml(self, stk, yaml_data):
        """test_tif_map_match_yaml method"""
        for k, v in yaml_data["tif_map"].items():
            assert stk.tif_map[k] == v, f"tif_map[{k}] mismatch"

    def test_rest_paths_match_yaml(self, stk, yaml_data):
        """test_rest_paths_match_yaml method"""
        yaml_stk_paths = yaml_data["asset_types"]["stk"]["rest_paths"]
        for k, v in yaml_stk_paths.items():
            assert stk.rest_paths[k] == v, f"rest_paths[{k}] mismatch"

    def test_wss_paths_match_yaml(self, stk, yaml_data):
        """test_wss_paths_match_yaml method"""
        yaml_stk_wss = yaml_data["asset_types"]["stk"]["wss_paths"]
        for k, v in yaml_stk_wss.items():
            assert stk.wss_paths[k] == v, f"wss_paths[{k}] mismatch"

    def test_rest_url_match_yaml(self, stk, yaml_data):
        """test_rest_url_match_yaml method"""
        assert stk.rest_url == yaml_data["base_urls"]["rest"]["default"]

    def test_wss_url_match_yaml(self, stk, yaml_data):
        """test_wss_url_match_yaml method"""
        assert stk.wss_url == yaml_data["base_urls"]["wss"]["default"]

    def test_rate_limits_match_yaml(self, stk, yaml_data):
        """rate_limits_config  == yaml limit/interval"""
        for rule in yaml_data["rate_limits"]:
            name = rule["name"]
            expected = rule["limit"] / rule["interval"]
            assert stk.rate_limits_config[name] == pytest.approx(expected), (
                f"rate_limits_config[{name}] mismatch"
            )


# ═══════════════════════════════════════════════════════════════
# 4.  IbWebExchangeData
# ═══════════════════════════════════════════════════════════════


class TestIbWebExchangeDataBase:
    """ IbWebExchangeData """

    @pytest.fixture
    def base(self):
        """base method"""
        return IbWebExchangeData()

    #
    def test_class_constants(self, base):
        """test_class_constants method"""
        assert base.PROD_REST_URL == "https://api.interactivebrokers.com"
        assert base.TEST_REST_URL == "https://api.test.interactivebrokers.com"
        assert base.GATEWAY_REST_URL == "https://localhost:5000"

    def test_rest_url_loaded(self, base):
        """test_rest_url_loaded method"""
        assert base.rest_url == "https://localhost:5000"

    # kline_periods
    @pytest.mark.kline
    def test_kline_periods_not_empty(self, base):
        """test_kline_periods_not_empty method"""
        assert len(base.kline_periods) > 0

    @pytest.mark.kline
    def test_kline_periods_keys(self, base):
        """test_kline_periods_keys method"""
        for k in ("1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w", "1M"):
            assert k in base.kline_periods

    @pytest.mark.kline
    def test_reverse_kline_periods(self, base):
        """test_reverse_kline_periods method"""
        for v, k in base.reverse_kline_periods.items():
            assert base.kline_periods[k] == v

    def test_get_period_known(self, base):
        """test_get_period_known method"""
        assert base.get_period("1h") == "1h"
        assert base.get_period("1m") == "1min"

    def test_get_period_unknown(self, base):
        """test_get_period_unknown method"""
        assert base.get_period("unknown") == "unknown"

    # sec_type_map
    def test_sec_type_map_not_empty(self, base):
        """test_sec_type_map_not_empty method"""
        assert len(base.sec_type_map) > 0

    def test_sec_type_map_values(self, base):
        """test_sec_type_map_values method"""
        assert base.sec_type_map["STK"] == "Stock"
        assert base.sec_type_map["FUT"] == "Future"
        assert base.sec_type_map["OPT"] == "Option"
        assert base.sec_type_map["FOP"] == "FutureOption"
        assert base.sec_type_map["CASH"] == "Forex"
        assert base.sec_type_map["CFD"] == "CFD"
        assert base.sec_type_map["BOND"] == "Bond"
        assert base.sec_type_map["CRYPTO"] == "Crypto"

    # market_data_fields
    def test_market_data_fields_not_empty(self, base):
        """test_market_data_fields_not_empty method"""
        assert len(base.market_data_fields) > 0

    def test_market_data_fields_core(self, base):
        """test_market_data_fields_core method"""
        assert base.market_data_fields["last_price"] == "31"
        assert base.market_data_fields["bid_price"] == "84"
        assert base.market_data_fields["bid_size"] == "85"
        assert base.market_data_fields["ask_price"] == "86"
        assert base.market_data_fields["ask_size"] == "88"
        assert base.market_data_fields["volume"] == "7059"

    def test_market_data_fields_ohlc(self, base):
        """test_market_data_fields_ohlc method"""
        assert base.market_data_fields["open"] == "7295"
        assert base.market_data_fields["high"] == "70"
        assert base.market_data_fields["low"] == "71"
        assert base.market_data_fields["close"] == "7291"

    def test_market_data_fields_change(self, base):
        """test_market_data_fields_change method"""
        assert base.market_data_fields["change"] == "82"
        assert base.market_data_fields["change_pct"] == "83"

    # default_snapshot_fields
    def test_default_snapshot_fields_not_empty(self, base):
        """test_default_snapshot_fields_not_empty method"""
        assert len(base.default_snapshot_fields) >= 6

    def test_default_snapshot_fields_content(self, base):
        """test_default_snapshot_fields_content method"""
        for f in ("31", "84", "85", "86", "88", "7059"):
            assert f in base.default_snapshot_fields

    # order_type_map
    def test_order_type_map_not_empty(self, base):
        """test_order_type_map_not_empty method"""
        assert len(base.order_type_map) > 0

    def test_order_type_map_values(self, base):
        """test_order_type_map_values method"""
        assert base.order_type_map["market"] == "MKT"
        assert base.order_type_map["limit"] == "LMT"
        assert base.order_type_map["stop"] == "STP"
        assert base.order_type_map["stop_limit"] == "STP_LMT"

    # tif_map
    def test_tif_map_not_empty(self, base):
        """test_tif_map_not_empty method"""
        assert len(base.tif_map) > 0

    def test_tif_map_values(self, base):
        """test_tif_map_values method"""
        assert base.tif_map["day"] == "DAY"
        assert base.tif_map["gtc"] == "GTC"
        assert base.tif_map["ioc"] == "IOC"
        assert base.tif_map["gtd"] == "GTD"

    # status_dict
    def test_status_dict_not_empty(self, base):
        """test_status_dict_not_empty method"""
        assert len(base.status_dict) > 0

    def test_status_dict_values(self, base):
        """test_status_dict_values method"""
        assert base.status_dict["submitted"] == "submit"
        assert base.status_dict["filled"] == "filled"
        assert base.status_dict["cancelled"] == "cancel"
        assert base.status_dict["inactive"] == "inactive"
        assert base.status_dict["presubmitted"] == "presubmit"

    # rate_limits_config
    def test_rate_limits_config_not_empty(self, base):
        """test_rate_limits_config_not_empty method"""
        assert len(base.rate_limits_config) > 0

    # get_symbol
    def test_get_symbol(self, base):
        """test_get_symbol method"""
        assert base.get_symbol("AAPL") == "AAPL"
        assert base.get_symbol("EUR.USD") == "EUR.USD"

    # get_snapshot_fields_str
    def test_get_snapshot_fields_str_default(self, base):
        """test_get_snapshot_fields_str_default method"""
        result = base.get_snapshot_fields_str()
        assert "31" in result
        assert "," in result

    def test_get_snapshot_fields_str_custom(self, base):
        """test_get_snapshot_fields_str_custom method"""
        assert base.get_snapshot_fields_str(fields=["31", "84"]) == "31,84"


# ═══════════════════════════════════════════════════════════════
# 5. REST
# ═══════════════════════════════════════════════════════════════


class TestRestPaths:
    """ REST """

    @pytest.fixture
    def stk(self):
        """stk method"""
        return IbWebExchangeDataStock()

    def test_rest_paths_not_empty(self, stk):
        """test_rest_paths_not_empty method"""
        assert len(stk.rest_paths) >= 40

    #
    def test_path_auth_status(self, stk):
        """test_path_auth_status method"""
        assert stk.rest_paths["auth_status"] == "POST /iserver/auth/status"

    def test_path_reauthenticate(self, stk):
        """test_path_reauthenticate method"""
        assert stk.rest_paths["reauthenticate"] == "POST /iserver/reauthenticate"

    def test_path_oauth_token(self, stk):
        """test_path_oauth_token method"""
        assert stk.rest_paths["oauth_token"] == "POST /oauth/token"

    #
    def test_path_search_stocks(self, stk):
        """test_path_search_stocks method"""
        assert stk.rest_paths["search_stocks"] == "GET /trsrv/stocks"

    def test_path_search_futures(self, stk):
        """test_path_search_futures method"""
        assert stk.rest_paths["search_futures"] == "GET /trsrv/futures"

    def test_path_secdef_search(self, stk):
        """test_path_secdef_search method"""
        assert stk.rest_paths["secdef_search"] == "GET /iserver/secdef/search"

    def test_path_secdef_strikes(self, stk):
        """test_path_secdef_strikes method"""
        assert stk.rest_paths["secdef_strikes"] == "GET /iserver/secdef/strikes"

    def test_path_secdef_info(self, stk):
        """test_path_secdef_info method"""
        assert stk.rest_paths["secdef_info"] == "GET /iserver/secdef/info"

    #
    def test_path_market_snapshot(self, stk):
        """test_path_market_snapshot method"""
        assert stk.rest_paths["market_snapshot"] == "GET /iserver/marketdata/snapshot"

    def test_path_market_history(self, stk):
        """test_path_market_history method"""
        assert stk.rest_paths["market_history"] == "GET /iserver/marketdata/history"

    @pytest.mark.ticker
    def test_path_get_tick(self, stk):
        """test_path_get_tick method"""
        assert stk.rest_paths["get_tick"] == "GET /iserver/marketdata/snapshot"

    @pytest.mark.orderbook
    def test_path_get_depth(self, stk):
        """test_path_get_depth method"""
        assert stk.rest_paths["get_depth"] == "GET /iserver/marketdata/snapshot"

    @pytest.mark.kline
    def test_path_get_kline(self, stk):
        """test_path_get_kline method"""
        assert stk.rest_paths["get_kline"] == "GET /iserver/marketdata/history"

    #
    def test_path_make_order(self, stk):
        """test_path_make_order method"""
        assert stk.rest_paths["make_order"] == "POST /iserver/account/{accountId}/orders"

    def test_path_modify_order(self, stk):
        """test_path_modify_order method"""
        assert stk.rest_paths["modify_order"] == "POST /iserver/account/{accountId}/order/{orderId}"

    def test_path_cancel_order(self, stk):
        """test_path_cancel_order method"""
        assert (
            stk.rest_paths["cancel_order"] == "DELETE /iserver/account/{accountId}/order/{orderId}"
        )

    def test_path_get_open_orders(self, stk):
        """test_path_get_open_orders method"""
        assert stk.rest_paths["get_open_orders"] == "GET /iserver/account/orders"

    def test_path_order_reply(self, stk):
        """test_path_order_reply method"""
        assert stk.rest_paths["order_reply"] == "POST /iserver/reply/{messageId}"

    def test_path_get_deals(self, stk):
        """test_path_get_deals method"""
        assert stk.rest_paths["get_deals"] == "GET /iserver/trades"

    #
    def test_path_portfolio_accounts(self, stk):
        """test_path_portfolio_accounts method"""
        assert stk.rest_paths["portfolio_accounts"] == "GET /portfolio/accounts"

    def test_path_get_position(self, stk):
        """test_path_get_position method"""
        assert stk.rest_paths["get_position"] == "GET /portfolio/{accountId}/positions"

    def test_path_get_account(self, stk):
        """test_path_get_account method"""
        assert stk.rest_paths["get_account"] == "GET /portfolio/{accountId}/summary"

    def test_path_get_balance(self, stk):
        """test_path_get_balance method"""
        assert stk.rest_paths["get_balance"] == "GET /portfolio/{accountId}/ledger"

    #  API
    def test_path_get_accounts_list(self, stk):
        """test_path_get_accounts_list method"""
        assert stk.rest_paths["get_accounts_list"] == "GET /gw/api/v1/accounts"

    def test_path_get_account_detail(self, stk):
        """test_path_get_account_detail method"""
        assert stk.rest_paths["get_account_detail"] == "GET /gw/api/v1/accounts/{accountId}"

    def test_path_update_account(self, stk):
        """test_path_update_account method"""
        assert stk.rest_paths["update_account"] == "PATCH /gw/api/v1/accounts/{accountId}"

    def test_path_close_account(self, stk):
        """test_path_close_account method"""
        assert stk.rest_paths["close_account"] == "POST /gw/api/v1/accounts/{accountId}/close"

    def test_path_bank_instructions(self, stk):
        """test_path_bank_instructions method"""
        assert stk.rest_paths["bank_instructions"] == "GET /gw/api/v1/bank-instructions/query"

    def test_path_withdraw_request(self, stk):
        """test_path_withdraw_request method"""
        assert stk.rest_paths["withdraw_request"] == "POST /gw/api/v1/withdraw-request"

    def test_path_deposit_request(self, stk):
        """test_path_deposit_request method"""
        assert stk.rest_paths["deposit_request"] == "POST /gw/api/v1/deposit-request"

    def test_path_internal_transfer(self, stk):
        """test_path_internal_transfer method"""
        assert stk.rest_paths["internal_transfer"] == "POST /gw/api/v1/internal-transfer"

    def test_path_statements(self, stk):
        """test_path_statements method"""
        assert stk.rest_paths["statements"] == "GET /gw/api/v1/statements"

    def test_path_tax_documents(self, stk):
        """test_path_tax_documents method"""
        assert stk.rest_paths["tax_documents"] == "GET /gw/api/v1/tax-documents/available"

    def test_path_trade_confirmations(self, stk):
        """test_path_trade_confirmations method"""
        assert stk.rest_paths["trade_confirmations"] == "GET /gw/api/v1/trade-confirmations"

    def test_path_sso_url(self, stk):
        """test_path_sso_url method"""
        assert stk.rest_paths["sso_url"] == "GET /gw/api/v1/sso/url"

    #
    def test_path_fyi_unread(self, stk):
        """test_path_fyi_unread method"""
        assert stk.rest_paths["fyi_unread"] == "GET /fyi/unreadnumber"

    def test_path_fyi_notifications(self, stk):
        """test_path_fyi_notifications method"""
        assert stk.rest_paths["fyi_notifications"] == "GET /fyi/notifications"

    def test_path_fyi_settings(self, stk):
        """test_path_fyi_settings method"""
        assert stk.rest_paths["fyi_settings"] == "GET /fyi/settings"

    #
    def test_path_not_found_raises(self, stk):
        """test_path_not_found_raises method"""
        with pytest.raises(NotImplementedError):
            stk.get_rest_path("nonexistent_path")


# ═══════════════════════════════════════════════════════════════
# 6. get_rest_url
# ═══════════════════════════════════════════════════════════════


class TestGetRestUrl:
    """ get_rest_url  METHOD +  + """

    @pytest.fixture
    def stk(self):
        """stk method"""
        return IbWebExchangeDataStock()

    def test_simple_get(self, stk):
        """test_simple_get method"""
        method, url = stk.get_rest_url("portfolio_accounts")
        assert method == "GET"
        assert url == "https://localhost:5000/portfolio/accounts"

    def test_get_with_account_param(self, stk):
        """test_get_with_account_param method"""
        method, url = stk.get_rest_url("get_position", accountId="U1234567")
        assert method == "GET"
        assert url == "https://localhost:5000/portfolio/U1234567/positions"

    def test_delete_with_two_params(self, stk):
        """test_delete_with_two_params method"""
        method, url = stk.get_rest_url("cancel_order", accountId="U1234567", orderId="99999")
        assert method == "DELETE"
        assert url == "https://localhost:5000/iserver/account/U1234567/order/99999"

    def test_post_with_account_param(self, stk):
        """test_post_with_account_param method"""
        method, url = stk.get_rest_url("make_order", accountId="U1234567")
        assert method == "POST"
        assert url == "https://localhost:5000/iserver/account/U1234567/orders"

    def test_post_modify_order(self, stk):
        """test_post_modify_order method"""
        method, url = stk.get_rest_url("modify_order", accountId="U1234567", orderId="12345")
        assert method == "POST"
        assert url == "https://localhost:5000/iserver/account/U1234567/order/12345"

    def test_patch_method(self, stk):
        """test_patch_method method"""
        method, url = stk.get_rest_url("update_account", accountId="U1234567")
        assert method == "PATCH"
        assert url == "https://localhost:5000/gw/api/v1/accounts/U1234567"

    def test_post_auth_status(self, stk):
        """test_post_auth_status method"""
        method, url = stk.get_rest_url("auth_status")
        assert method == "POST"
        assert url == "https://localhost:5000/iserver/auth/status"

    def test_post_order_reply(self, stk):
        """test_post_order_reply method"""
        method, url = stk.get_rest_url("order_reply", messageId="abc123")
        assert method == "POST"
        assert url == "https://localhost:5000/iserver/reply/abc123"

    def test_get_balance(self, stk):
        """test_get_balance method"""
        method, url = stk.get_rest_url("get_balance", accountId="U9999999")
        assert method == "GET"
        assert url == "https://localhost:5000/portfolio/U9999999/ledger"

    def test_get_account_detail(self, stk):
        """test_get_account_detail method"""
        method, url = stk.get_rest_url("get_account_detail", accountId="U1234567")
        assert method == "GET"
        assert url == "https://localhost:5000/gw/api/v1/accounts/U1234567"


# ═══════════════════════════════════════════════════════════════
# 7. WebSocket
# ═══════════════════════════════════════════════════════════════


class TestWssPaths:
    """ WebSocket """

    @pytest.fixture
    def stk(self):
        """stk method"""
        return IbWebExchangeDataStock()

    def test_wss_paths_count(self, stk):
        """test_wss_paths_count method"""
        assert len(stk.wss_paths) == 7

    def test_wss_market_data(self, stk):
        """test_wss_market_data method"""
        assert stk.wss_paths["market_data"] == "smd+{conid}+{fields_json}"

    def test_wss_unsubscribe(self, stk):
        """test_wss_unsubscribe method"""
        assert stk.wss_paths["unsubscribe"] == "umd+{conid}+{}"

    def test_wss_account(self, stk):
        """test_wss_account method"""
        assert stk.wss_paths["account"] == "sacct"

    def test_wss_orders(self, stk):
        """test_wss_orders method"""
        assert stk.wss_paths["orders"] == "sor"

    def test_wss_pnl(self, stk):
        """test_wss_pnl method"""
        assert stk.wss_paths["pnl"] == "spl+{accountId}"

    def test_wss_trades(self, stk):
        """test_wss_trades method"""
        assert stk.wss_paths["trades"] == "str"

    def test_wss_heartbeat(self, stk):
        """test_wss_heartbeat method"""
        assert stk.wss_paths["heartbeat"] == "tic"

    def test_get_wss_path(self, stk):
        """test_get_wss_path method"""
        assert stk.get_wss_path() == "wss://localhost:5000/v1/api/ws"


# ═══════════════════════════════════════════════════════════════
# 8.  exchange_name
# ═══════════════════════════════════════════════════════════════


class TestSubclassExchangeNames:
    """ exchange_name"""

    def test_stock(self):
        """test_stock method"""
        assert IbWebExchangeDataStock().exchange_name == "IB_WEB_STK"

    def test_future(self):
        """test_future method"""
        assert IbWebExchangeDataFuture().exchange_name == "IB_WEB_FUT"

    def test_option(self):
        """test_option method"""
        assert IbWebExchangeDataOption().exchange_name == "IB_WEB_OPT"

    def test_forex(self):
        """test_forex method"""
        assert IbWebExchangeDataForex().exchange_name == "IB_WEB_CASH"


# ═══════════════════════════════════════════════════════════════
# 9.
# ═══════════════════════════════════════════════════════════════


class TestSubclassConsistency:
    """ ( yaml)"""

    @pytest.fixture
    def all_instances(self):
        """all_instances method"""
        return {
            "stk": IbWebExchangeDataStock(),
            "fut": IbWebExchangeDataFuture(),
            "opt": IbWebExchangeDataOption(),
            "cash": IbWebExchangeDataForex(),
        }

    def test_same_rest_url(self, all_instances):
        """test_same_rest_url method"""
        urls = {v.rest_url for v in all_instances.values()}
        assert len(urls) == 1

    def test_same_wss_url(self, all_instances):
        """test_same_wss_url method"""
        urls = {v.wss_url for v in all_instances.values()}
        assert len(urls) == 1

    @pytest.mark.kline
    def test_same_kline_periods(self, all_instances):
        """test_same_kline_periods method"""
        ref = list(all_instances.values())[0].kline_periods
        for v in all_instances.values():
            assert v.kline_periods == ref

    def test_same_status_dict(self, all_instances):
        """test_same_status_dict method"""
        ref = list(all_instances.values())[0].status_dict
        for v in all_instances.values():
            assert v.status_dict == ref

    def test_same_sec_type_map(self, all_instances):
        """test_same_sec_type_map method"""
        ref = list(all_instances.values())[0].sec_type_map
        for v in all_instances.values():
            assert v.sec_type_map == ref

    def test_same_market_data_fields(self, all_instances):
        """test_same_market_data_fields method"""
        ref = list(all_instances.values())[0].market_data_fields
        for v in all_instances.values():
            assert v.market_data_fields == ref

    def test_same_default_snapshot_fields(self, all_instances):
        """test_same_default_snapshot_fields method"""
        ref = list(all_instances.values())[0].default_snapshot_fields
        for v in all_instances.values():
            assert v.default_snapshot_fields == ref

    def test_same_order_type_map(self, all_instances):
        """test_same_order_type_map method"""
        ref = list(all_instances.values())[0].order_type_map
        for v in all_instances.values():
            assert v.order_type_map == ref

    def test_same_tif_map(self, all_instances):
        """test_same_tif_map method"""
        ref = list(all_instances.values())[0].tif_map
        for v in all_instances.values():
            assert v.tif_map == ref

    def test_same_rate_limits_config(self, all_instances):
        """test_same_rate_limits_config method"""
        ref = list(all_instances.values())[0].rate_limits_config
        for v in all_instances.values():
            assert v.rate_limits_config == ref

    def test_same_rest_paths_keys(self, all_instances):
        """test_same_rest_paths_keys method"""
        ref = set(list(all_instances.values())[0].rest_paths.keys())
        for v in all_instances.values():
            assert set(v.rest_paths.keys()) == ref

    def test_same_wss_paths_keys(self, all_instances):
        """test_same_wss_paths_keys method"""
        ref = set(list(all_instances.values())[0].wss_paths.keys())
        for v in all_instances.values():
            assert set(v.wss_paths.keys()) == ref

    def test_different_exchange_names(self, all_instances):
        """test_different_exchange_names method"""
        names = [v.exchange_name for v in all_instances.values()]
        assert len(set(names)) == 4


# ═══════════════════════════════════════════════════════════════
# 10.
# ═══════════════════════════════════════════════════════════════


class TestRateLimits:
    """ ( yaml rate_limits )"""

    @pytest.fixture
    def base(self):
        """base method"""
        return IbWebExchangeData()

    def test_rate_limits_not_empty(self, base):
        """test_rate_limits_not_empty method"""
        assert len(base.rate_limits_config) >= 5

    def test_global_trading_limit(self, base):
        """test_global_trading_limit method"""
        assert base.rate_limits_config["global_trading"] == pytest.approx(50.0)

    def test_cp_gateway_limit(self, base):
        """test_cp_gateway_limit method"""
        assert base.rate_limits_config["cp_gateway"] == pytest.approx(10.0)

    def test_account_management_limit(self, base):
        """test_account_management_limit method"""
        assert base.rate_limits_config["account_management"] == pytest.approx(10.0)

    def test_market_snapshot_limit(self, base):
        """test_market_snapshot_limit method"""
        assert base.rate_limits_config["market_snapshot"] == pytest.approx(10.0)

    def test_orders_query_limit(self, base):
        """test_orders_query_limit method"""
        assert base.rate_limits_config["orders_query"] == pytest.approx(0.2)


# ═══════════════════════════════════════════════════════════════
# 11. ExchangeData
# ═══════════════════════════════════════════════════════════════


class TestExchangeDataInheritance:
    """ ExchangeData """

    def test_is_exchange_data_instance(self):
        """test_is_exchange_data_instance method"""
        from bt_api_base.containers.exchanges.exchange_data import ExchangeData

        for cls in (
            IbWebExchangeDataStock,
            IbWebExchangeDataFuture,
            IbWebExchangeDataOption,
            IbWebExchangeDataForex,
        ):
            assert isinstance(cls(), ExchangeData)

    def test_to_dict(self):
        """test_to_dict method"""
        d = IbWebExchangeDataStock().to_dict()
        assert isinstance(d, dict)
        for key in ("exchange_name", "rest_url", "kline_periods"):
            assert key in d

    def test_raise_path_error(self):
        """test_raise_path_error method"""
        with pytest.raises(NotImplementedError):
            IbWebExchangeDataStock().raise_path_error("IB_WEB_STK", "nonexistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
