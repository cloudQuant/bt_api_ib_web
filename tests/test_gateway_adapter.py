from __future__ import annotations

import pytest

from bt_api_ib_web.gateway import adapter as adapter_module


class _FakeFeed:
    def __init__(
        self,
        balance=None,
        positions=None,
        stock_search=None,
        contract_search=None,
        contract_details=None,
    ):
        self.orders = []
        self.cancel_calls = []
        self.balance = balance or {}
        self.positions = positions or []
        self.stock_search = stock_search or {}
        self.contract_search = contract_search or []
        self.contract_details = contract_details or {}
        self.detail_calls = 0

    def get_balance(self):
        return self.balance

    def get_position(self):
        return self.positions

    def search_stocks(self, symbol):
        return self.stock_search

    def search_contract(self, symbol, sec_type="STK"):
        return self.contract_search

    def resolve_conid(self, symbol, sec_type="STK"):
        if self.contract_details.get("conid") is not None:
            return self.contract_details["conid"]
        return None

    def _get(self, path, params=None):
        if path == "/iserver/secdef/info":
            self.detail_calls += 1
            return self.contract_details
        return {}

    def make_order(
        self,
        symbol,
        volume,
        price,
        order_type,
        client_order_id=None,
        extra_data=None,
    ):
        self.orders.append(
            {
                "symbol": symbol,
                "volume": volume,
                "price": price,
                "order_type": order_type,
                "client_order_id": client_order_id,
                "extra_data": dict(extra_data or {}),
            }
        )
        return {"orderId": "ib-1", "status": "Submitted"}

    def cancel_order(self, symbol, order_id, extra_data=None):
        self.cancel_calls.append(
            {"symbol": symbol, "order_id": order_id, "extra_data": dict(extra_data or {})}
        )
        return {"orderId": order_id, "status": "Cancelled"}


def test_place_order_preserves_sell_side_for_canonical_stop_limit(monkeypatch):
    feed = _FakeFeed()
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    result = adapter.place_order(
        {
            "symbol": "AAPL",
            "side": "sell",
            "size": 10,
            "price": 189.5,
            "order_type": "stop_limit",
            "stop_price": 190.0,
            "bt_order_ref": "bt-9",
        }
    )

    assert result["id"] == "ib-1"
    sent = feed.orders[0]
    assert sent["order_type"] == "sell-stop_limit"
    assert sent["price"] == 189.5
    assert sent["extra_data"]["aux_price"] == 190.0
    assert sent["client_order_id"] == "bt-9"


def test_cancel_order_accepts_gateway_order_ref_alias(monkeypatch):
    feed = _FakeFeed()
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    result = adapter.cancel_order({"instrument": "AAPL", "order_ref": "ib-987"})

    assert result["order_id"] == "ib-987"
    assert result["status"] == "Cancelled"
    assert feed.cancel_calls == [
        {"symbol": "AAPL", "order_id": "ib-987", "extra_data": {}}
    ]


def test_get_balance_prefers_available_funds_for_cash(monkeypatch):
    feed = _FakeFeed(
        {
            "CashBalance": "100000",
            "AvailableFunds": "85000",
            "NetLiquidation": "101500",
            "EquityWithLoanValue": "101000",
            "InitMarginReq": "15000",
            "MaintMarginReq": "12000",
            "BuyingPower": "340000",
            "UnrealizedPnL": "1500",
        }
    )
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    result = adapter.get_balance()

    assert result["cash"] == 85000.0
    assert result["available"] == 85000.0
    assert result["available_funds"] == 85000.0
    assert result["balance"] == 100000.0
    assert result["value"] == 101500.0
    assert result["equity"] == 101500.0
    assert result["margin"] == 15000.0
    assert result["used_margin"] == 15000.0
    assert result["buying_power"] == 340000.0
    assert result["unrealized_pnl"] == 1500.0


def test_get_balance_keeps_zero_available_funds(monkeypatch):
    feed = _FakeFeed(
        {
            "CashBalance": {"amount": "100000", "currency": "USD"},
            "AvailableFunds": {"amount": "0", "currency": "USD"},
            "NetLiquidation": {"amount": "250000", "currency": "USD"},
        }
    )
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    result = adapter.get_balance()

    assert result["cash"] == 0.0
    assert result["available_funds"] == 0.0
    assert result["balance"] == 100000.0
    assert result["value"] == 250000.0


def test_get_balance_derives_available_cash_from_value_minus_margin(monkeypatch):
    feed = _FakeFeed(
        {
            "CashBalance": "100,000",
            "NetLiquidation": "101,500",
            "InitMarginReq": "15,000",
        }
    )
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="FUT")

    result = adapter.get_balance()

    assert result["cash"] == 86500.0
    assert result["available"] == 86500.0
    assert result["available_funds"] == 86500.0
    assert result["balance"] == 100000.0
    assert result["value"] == 101500.0
    assert result["equity"] == 101500.0
    assert result["margin"] == 15000.0


def test_get_positions_normalizes_ib_portfolio_rows(monkeypatch):
    feed = _FakeFeed(
        positions=[
            {
                "account": "U123456",
                "symbol": "AAPL",
                "secType": "STK",
                "position": 10,
                "avgCost": 150.0,
                "marketPrice": 155.0,
                "marketValue": 1550.0,
                "unrealizedPNL": 50.0,
                "realizedPNL": 12.5,
                "currency": "USD",
            }
        ]
    )
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    result = adapter.get_positions()

    assert result == [
        {
            "account": "U123456",
            "symbol": "AAPL",
            "instrument": "AAPL",
            "data_name": "AAPL",
            "secType": "STK",
            "sec_type": "STK",
            "asset_type": "STK",
            "position": 10,
            "size": 10.0,
            "volume": 10.0,
            "avgCost": 150.0,
            "price": 150.0,
            "avg_price": 150.0,
            "marketPrice": 155.0,
            "current_price": 155.0,
            "latest_price": 155.0,
            "last_price": 155.0,
            "marketValue": 1550.0,
            "market_value": 1550.0,
            "unrealizedPNL": 50.0,
            "unrealized_pnl": 50.0,
            "gross_pnl": 50.0,
            "realizedPNL": 12.5,
            "realized_pnl": 12.5,
            "currency": "USD",
            "direction": "long",
        }
    ]


def test_get_positions_normalizes_ib_client_portal_field_names(monkeypatch):
    """IBKR Client Portal positions use mkt*/Pnl field names in examples."""
    feed = _FakeFeed(
        positions=[
            {
                "acctId": "U123456",
                "contractDesc": "SPY",
                "assetClass": "STK",
                "position": 5.0,
                "avgPrice": 434.93,
                "mktPrice": 471.16000365,
                "mktValue": 2355.8,
                "unrealizedPnl": 181.15,
                "realizedPnl": 0.0,
                "currency": "USD",
            }
        ]
    )
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    result = adapter.get_positions()[0]

    assert result["symbol"] == "SPY"
    assert result["instrument"] == "SPY"
    assert result["data_name"] == "SPY"
    assert result["asset_type"] == "STK"
    assert result["sec_type"] == "STK"
    assert result["size"] == 5.0
    assert result["price"] == 434.93
    assert result["current_price"] == 471.16000365
    assert result["latest_price"] == 471.16000365
    assert result["market_value"] == 2355.8
    assert result["unrealized_pnl"] == 181.15
    assert result["gross_pnl"] == 181.15
    assert result["realized_pnl"] == 0.0


def test_get_symbol_info_uses_stock_search_and_contract_details(monkeypatch):
    feed = _FakeFeed(
        stock_search={
            "AAPL": [
                {
                    "name": "APPLE INC",
                    "contracts": [
                        {
                            "conid": 265598,
                            "exchange": "NASDAQ",
                        }
                    ],
                }
            ]
        },
        contract_details={
            "conid": 265598,
            "symbol": "AAPL",
            "secType": "STK",
            "currency": "USD",
            "minTick": "0.01",
        },
    )
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    result = adapter.get_symbol_info("AAPL")
    cached = adapter.get_symbol_info("AAPL")

    assert result["source"] == "ib_web_gateway"
    assert result["symbol"] == "AAPL"
    assert result["conid"] == 265598
    assert result["secType"] == "STK"
    assert result["currency"] == "USD"
    assert result["price_tick"] == 0.01
    assert result["contract_size"] == 1.0
    assert cached == result
    assert feed.detail_calls == 1


def test_get_symbol_info_uses_future_contract_multiplier(monkeypatch):
    feed = _FakeFeed(
        contract_search=[
            {
                "conid": 495512552,
                "symbol": "ES",
                "secType": "FUT",
                "exchange": "CME",
            }
        ],
        contract_details={
            "conid": 495512552,
            "symbol": "ES",
            "secType": "FUT",
            "exchange": "CME",
            "currency": "USD",
            "multiplier": "50",
            "minTick": "0.25",
            "lastTradingDay": "20250620",
        },
    )
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="FUT")

    result = adapter.get_symbol_info("ES")

    assert result["source"] == "ib_web_gateway"
    assert result["symbol"] == "ES"
    assert result["contract_size"] == 50.0
    assert result["contract_multiplier"] == 50.0
    assert result["price_tick"] == 0.25
    assert result["last_trade_date"] == "20250620"


def test_place_order_defaults_blank_type_with_payload_side(monkeypatch):
    feed = _FakeFeed()
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    adapter.place_order({"symbol": "AAPL", "side": "sell", "size": 10, "price": 189.5})

    assert feed.orders[0]["order_type"] == "sell-limit"


def test_place_order_rejects_stop_limit_without_limit_price(monkeypatch):
    feed = _FakeFeed()
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    with pytest.raises(ValueError, match="stop-limit orders require"):
        adapter.place_order(
            {
                "symbol": "AAPL",
                "side": "sell",
                "size": 10,
                "order_type": "stop_limit",
                "stop_price": 190.0,
            }
        )

    assert feed.orders == []


def test_place_order_rejects_stop_without_trigger(monkeypatch):
    feed = _FakeFeed()
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    with pytest.raises(ValueError, match="stop orders require"):
        adapter.place_order({"symbol": "AAPL", "side": "sell", "size": 10, "order_type": "stop"})

    assert feed.orders == []


def test_place_order_maps_stop_price_to_aux_price(monkeypatch):
    feed = _FakeFeed()
    monkeypatch.setattr(adapter_module, "_create_feed", lambda _queue, _kwargs: feed)
    adapter = adapter_module.IbWebGatewayAdapter(asset_type="STK")

    adapter.place_order(
        {
            "symbol": "AAPL",
            "side": "sell",
            "size": 10,
            "price": 190.0,
            "order_type": "stop",
        }
    )

    sent = feed.orders[0]
    assert sent["order_type"] == "sell-stop"
    assert sent["extra_data"]["aux_price"] == 190.0
