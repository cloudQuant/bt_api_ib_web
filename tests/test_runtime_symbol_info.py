"""Direct Client Portal contract metadata projection tests."""

from __future__ import annotations

from bt_api_ib_web.runtime.feed import IbWebRequestData


def _feed(asset_type: str = "STK") -> IbWebRequestData:
    feed = object.__new__(IbWebRequestData)
    feed.asset_type = asset_type
    feed._symbol_info_cache = {}
    return feed


def test_stock_symbol_info_uses_search_and_contract_details(monkeypatch) -> None:
    feed = _feed()
    calls = []
    monkeypatch.setattr(
        feed,
        "search_stocks",
        lambda symbol: {symbol: [{"contracts": [{"conid": 265598, "exchange": "NASDAQ"}]}]},
    )
    monkeypatch.setattr(
        feed,
        "search_contract",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("stock search should resolve")),
    )
    monkeypatch.setattr(
        feed,
        "_get",
        lambda path, params=None: calls.append((path, params))
        or [{"minTick": 0.01, "currency": "USD", "localSymbol": "AAPL"}],
    )

    spec = feed.get_symbol_info("AAPL")
    cached = feed.get_symbol_info("265598")

    assert spec["source"] == "ib_web_direct"
    assert spec["symbol"] == spec["data_name"] == spec["instrument"] == "AAPL"
    assert spec["secType"] == spec["sec_type"] == spec["asset_type"] == "STK"
    assert spec["exchange"] == spec["exchange_id"] == "NASDAQ"
    assert spec["currency"] == "USD"
    assert spec["localSymbol"] == spec["local_symbol"] == "AAPL"
    assert spec["conid"] == spec["contract_id"] == 265598
    assert spec["multiplier"] == spec["contract_multiplier"] == 1.0
    assert spec["price_tick"] == spec["tick_size"] == 0.01
    assert "last_trade_date" not in spec
    assert calls == [("/iserver/secdef/info", {"conid": "265598"})]
    assert feed._symbol_info_cache["STK:AAPL"] == spec
    assert feed._symbol_info_cache["STK:265598"] == spec
    assert cached == spec


def test_future_symbol_info_preserves_contract_multiplier_and_expiry(monkeypatch) -> None:
    feed = _feed("FUT")
    search_calls = []
    detail_calls = []
    monkeypatch.setattr(
        feed,
        "search_stocks",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("not a stock")),
    )

    def search_contract(symbol, sec_type):
        search_calls.append((symbol, sec_type))
        return [
            {"symbol": symbol, "conid": 12345, "secType": sec_type, "exchange": "CME"}
        ]

    def get_details(path, params=None):
        detail_calls.append((path, params))
        return {
            "conid": 12345,
            "multiplier": "50",
            "minTick": "0.25",
            "lastTradingDay": "20261218",
            "currency": "USD",
            "localSymbol": "ESH7",
        }

    monkeypatch.setattr(feed, "search_contract", search_contract)
    monkeypatch.setattr(feed, "_get", get_details)

    spec = feed.get_symbol_info("ES", "FUT")
    cached_by_conid = feed.get_symbol_info("12345", "FUT")
    cached_by_local_symbol = feed.get_symbol_info("ESH7", "FUT")

    assert spec["source"] == "ib_web_direct"
    assert spec["symbol"] == spec["data_name"] == spec["instrument"] == "ES"
    assert spec["secType"] == spec["sec_type"] == spec["asset_type"] == "FUT"
    assert spec["exchange"] == spec["exchange_id"] == "CME"
    assert spec["currency"] == "USD"
    assert spec["localSymbol"] == spec["local_symbol"] == "ESH7"
    assert spec["conid"] == 12345
    assert (
        spec["multiplier"]
        == spec["contract_multiplier"]
        == spec["contract_size"]
        == 50.0
    )
    assert spec["price_tick"] == 0.25
    assert spec["last_trade_date"] == "20261218"
    assert search_calls == [("ES", "FUT")]
    assert detail_calls == [("/iserver/secdef/info", {"conid": "12345"})]
    assert feed._symbol_info_cache["FUT:ES"] == spec
    assert feed._symbol_info_cache["FUT:12345"] == spec
    assert feed._symbol_info_cache["FUT:ESH7"] == spec
    assert cached_by_conid == cached_by_local_symbol == spec

