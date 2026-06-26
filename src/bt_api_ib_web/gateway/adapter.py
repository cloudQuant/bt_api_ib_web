from __future__ import annotations

import queue
import threading
import time
from collections import defaultdict
from typing import Any

from bt_api_base.gateway.adapters.base import BaseGatewayAdapter
from bt_api_base.gateway.models import GatewayTick
from bt_api_base.gateway.protocol import CHANNEL_EVENT, CHANNEL_MARKET

from bt_api_ib_web.runtime.feed import IbWebRequestDataFuture, IbWebRequestDataStock
from bt_api_ib_web.runtime.stream import IbWebAccountStream, IbWebDataStream


class IbWebGatewayAdapter(BaseGatewayAdapter):
    def __init__(self, **kwargs: Any) -> None:
        normalized = dict(kwargs)
        self.asset_type = _normalize_asset_type(normalized.get('asset_type'))
        normalized['asset_type'] = self.asset_type
        normalized['base_url'] = (
            normalized.get('base_url')
            or normalized.get('rest_url')
            or 'https://localhost:5000'
        )
        super().__init__(**normalized)
        self.kwargs = normalized
        self.q: queue.Queue[Any] = queue.Queue()
        self.feed = _create_feed(self.q, normalized)
        self.market_stream: IbWebDataStream | None = None
        self.account_stream: IbWebAccountStream | None = None
        self.aliases: dict[int, set[str]] = defaultdict(set)
        self._symbol_specs: dict[str, dict[str, Any]] = {}
        self.running = False
        self.thread: threading.Thread | None = None
        self.timeout = float(
            normalized.get('gateway_startup_timeout_sec', 10.0) or 10.0
        )

    def connect(self) -> None:
        if self.running:
            return
        self.feed.connect()
        if not self.feed.is_connected():
            cause = getattr(self.feed, 'get_last_connect_error', lambda: None)()
            if cause is not None:
                raise RuntimeError(
                    f'ib_web feed not ready: {type(cause).__name__}: {cause}'
                ) from cause
            raise RuntimeError('ib_web feed not ready')
        self._ensure_account_stream()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def disconnect(self) -> None:
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        if self.market_stream is not None:
            self.market_stream.stop()
        if self.account_stream is not None:
            self.account_stream.stop()
        self.feed.disconnect()
        self.market_stream = None
        self.account_stream = None

    def subscribe_symbols(self, symbols: list[str]) -> dict[str, Any]:
        done: list[str] = []
        topics: list[dict[str, Any]] = []
        for raw in symbols:
            alias = str(raw or '').strip()
            if not alias:
                continue
            conid = int(self.feed._resolve_conid_param(alias))
            self.aliases[conid].update({alias, str(conid)})
            topics.append({'topic': 'market_data', 'conid': conid})
            done.append(alias)
        if topics:
            self._ensure_market_stream(topics)
        return {'symbols': done}

    def get_balance(self) -> dict[str, Any]:
        response = self.feed.get_balance()
        if isinstance(response, dict):
            available_cash = _first_float(
                response,
                ('available', 'available_funds', 'availablefunds', 'AvailableFunds', 'cash'),
                None,
            )
            cash_balance = _first_float(
                response,
                ('balance', 'CashBalance', 'cashbalance', 'TotalCashValue', 'totalcashvalue'),
                None,
            )
            value = _first_float(
                response,
                ('value', 'equity', 'NetLiquidation', 'netliquidation', 'EquityWithLoanValue'),
                None,
            )
            used_margin = _first_float(
                response,
                ('margin', 'used_margin', 'InitMarginReq', 'initmarginreq', 'MaintMarginReq'),
                None,
            )
            buying_power = _first_float(
                response, ('buying_power', 'buyingpower', 'BuyingPower'), None
            )
            unrealized_pnl = _first_float(
                response, ('unrealized_pnl', 'UnrealizedPnL', 'unrealizedpnl'), None
            )
            if available_cash is None and value is not None and used_margin is not None:
                available_cash = value - used_margin
            if available_cash is None:
                available_cash = cash_balance if cash_balance is not None else 0.0
            if cash_balance is None:
                cash_balance = available_cash
            if value is None:
                value = cash_balance
            payload = dict(response)
            payload['cash'] = available_cash
            payload['available'] = available_cash
            payload['available_funds'] = available_cash
            payload['balance'] = cash_balance
            payload['value'] = value
            payload['equity'] = value
            if used_margin is not None:
                payload.setdefault('margin', used_margin)
                payload.setdefault('used_margin', used_margin)
            if buying_power is not None:
                payload.setdefault('buying_power', buying_power)
            if unrealized_pnl is not None:
                payload.setdefault('unrealized_pnl', unrealized_pnl)
            return payload
        return {'cash': 0.0, 'value': 0.0, 'raw': response}

    def get_positions(self) -> list[dict[str, Any]]:
        try:
            response = self.feed.get_position()
        except NotImplementedError:
            return []
        rows: list[dict[str, Any]]
        if isinstance(response, list):
            rows = [item for item in response if isinstance(item, dict)]
        elif isinstance(response, dict):
            rows = response.get('positions')
            if isinstance(rows, list):
                rows = [item for item in rows if isinstance(item, dict)]
            else:
                rows = [response]
        else:
            rows = []
        return [_normalize_position_row(item, self.asset_type) for item in rows]

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        key = str(symbol or '').strip()
        if not key:
            return {}
        cached = self._symbol_specs.get(key)
        if cached:
            return dict(cached)
        spec = _ib_symbol_spec(self.feed, key, self.asset_type)
        if spec:
            for cache_key in (
                key,
                spec.get('symbol'),
                spec.get('localSymbol'),
                spec.get('local_symbol'),
                spec.get('conid'),
                spec.get('contract_id'),
            ):
                cache_text = str(cache_key or '').strip()
                if cache_text:
                    self._symbol_specs[cache_text] = dict(spec)
        return spec

    def place_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        symbol = str(payload.get('data_name') or payload.get('symbol') or '').strip()
        side = str(payload.get('side') or 'buy').lower()
        order_type = str(payload.get('order_type') or '').strip().lower()
        if not order_type:
            order_type = (
                f'{side}-{"market" if payload.get("price") in (None, "") else "limit"}'
            )
        else:
            order_type = _order_type_with_side(side, order_type)
        extra_data = dict(payload.get('extra_data') or {})
        stop_price = payload.get('stop_price') or payload.get('trigger_price')
        if stop_price in (None, '') and _is_stop_order_type(order_type):
            stop_price = extra_data.get('aux_price')
        if (
            stop_price in (None, '')
            and _is_stop_order_type(order_type)
            and not _is_stop_limit_order_type(order_type)
            and payload.get('price') not in (None, '')
        ):
            stop_price = payload.get('price')
        if stop_price not in (None, ''):
            extra_data.setdefault('aux_price', stop_price)
        if _is_stop_order_type(order_type) and extra_data.get('aux_price') in (None, ''):
            raise ValueError('IB Web stop orders require stop_price or extra_data.aux_price')
        if _is_stop_limit_order_type(order_type) and payload.get('price') in (None, ''):
            raise ValueError('IB Web stop-limit orders require a positive limit price')
        response = self.feed.make_order(
            symbol,
            volume=payload.get('size') or payload.get('volume') or 0,
            price=payload.get('price'),
            order_type=order_type,
            client_order_id=payload.get('client_order_id')
            or payload.get('bt_order_ref'),
            extra_data=extra_data,
        )
        row = _first_row(response)
        order_id = (
            row.get('order_id')
            or row.get('orderId')
            or row.get('id')
            or payload.get('client_order_id')
            or payload.get('bt_order_ref')
            or ''
        )
        return {
            'id': order_id,
            'order_id': order_id,
            'external_order_id': row.get('orderId') or row.get('id') or order_id,
            'details': row or response,
        }

    def cancel_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        symbol = str(
            payload.get('data_name')
            or payload.get('symbol')
            or payload.get('instrument')
            or ''
        ).strip()
        order_id = (
            payload.get('order_id')
            or payload.get('external_order_id')
            or payload.get('venue_order_id')
            or payload.get('id')
            or payload.get('order_ref')
        )
        extra_data = dict(payload.get('extra_data') or {})
        response = self.feed.cancel_order(symbol, order_id, extra_data=extra_data)
        row = _first_row(response)
        return {
            'id': row.get('orderId') or order_id,
            'order_id': row.get('orderId') or order_id,
            'status': row.get('status') or row.get('order_status') or 'canceled',
            'details': row or response,
        }

    def _ensure_market_stream(self, topics: list[dict[str, Any]]) -> None:
        if self.market_stream is None or not self.market_stream.is_running():
            self.market_stream = IbWebDataStream(self.q, **self.kwargs, topics=topics)
            self.market_stream.start()
            if not self.market_stream.wait_connected(timeout=self.timeout):
                raise RuntimeError('ib_web market stream not ready')
            return
        self.market_stream.subscribe_topics(topics)

    def _ensure_account_stream(self) -> None:
        if self.account_stream is not None and self.account_stream.is_running():
            return
        topics = [{'topic': 'account'}, {'topic': 'order'}, {'topic': 'trade'}]
        self.account_stream = IbWebAccountStream(self.q, **self.kwargs, topics=topics)
        self.account_stream.start()
        if not self.account_stream.wait_connected(timeout=self.timeout):
            raise RuntimeError('ib_web account stream not ready')

    def _run(self) -> None:
        while self.running:
            try:
                item = self.q.get(timeout=0.2)
            except queue.Empty:
                continue
            if isinstance(item, dict):
                self._handle_item(item)

    def _handle_item(self, item: dict[str, Any]) -> None:
        item_type = str(item.get('type') or '').strip().lower()
        data = dict(item.get('data') or {})
        if item_type == 'market_data':
            self._emit_market(data)
            return
        kind = {
            'order_update': 'order',
            'trade_update': 'trade',
            'account_update': 'account',
            'pnl_update': 'pnl',
        }.get(item_type, item_type or 'system')
        self.emit(CHANNEL_EVENT, {'kind': kind, 'exchange': 'IB_WEB', 'data': data})

    def _emit_market(self, data: dict[str, Any]) -> None:
        conid_raw = (
            data.get('conidEx')
            or data.get('conid')
            or data.get('contract_id')
            or _conid_from_topic(data.get('topic'))
            or ''
        )
        alias_candidates = self.aliases.get(_safe_int(conid_raw), set()) or {
            str(data.get('symbol') or conid_raw or '')
        }
        now = time.time()
        price = _coerce_float(
            data.get('31') or data.get('last') or data.get('lastPrice'), 0.0
        )
        bid_price = _coerce_float(
            data.get('84') or data.get('bid') or data.get('bidPrice'), None
        )
        ask_price = _coerce_float(
            data.get('86') or data.get('ask') or data.get('askPrice'), None
        )
        bid_volume = _coerce_float(
            data.get('85') or data.get('bidSize') or data.get('bid_volume'), None
        )
        ask_volume = _coerce_float(
            data.get('88') or data.get('askSize') or data.get('ask_volume'), None
        )
        volume = _coerce_float(
            data.get('volume') or data.get('lastSize') or data.get('87'), 0.0
        )
        instrument_id = str(conid_raw or data.get('symbol') or '')
        exchange_id = str(data.get('exchange') or data.get('listingExchange') or '')
        for alias in alias_candidates:
            if not alias:
                continue
            self.emit(
                CHANNEL_MARKET,
                GatewayTick(
                    timestamp=now,
                    local_time=now,
                    symbol=alias,
                    exchange='IB_WEB',
                    asset_type=self.asset_type.lower(),
                    price=price or 0.0,
                    volume=volume or 0.0,
                    bid_price=bid_price,
                    ask_price=ask_price,
                    bid_volume=bid_volume,
                    ask_volume=ask_volume,
                    instrument_id=instrument_id,
                    exchange_id=exchange_id,
                ),
            )


def _normalize_asset_type(value: Any) -> str:
    text = str(value or 'STK').strip().upper()
    if text in {'STOCK', 'STK', 'EQUITY'}:
        return 'STK'
    if text in {'FUTURE', 'FUT'}:
        return 'FUT'
    return text or 'STK'


def _create_feed(data_queue: Any, kwargs: dict[str, Any]) -> Any:
    if _normalize_asset_type(kwargs.get('asset_type')) == 'FUT':
        return IbWebRequestDataFuture(data_queue, **kwargs)
    return IbWebRequestDataStock(data_queue, **kwargs)


def _order_type_with_side(side: Any, order_type: Any) -> str:
    normalized_side = 'sell' if str(side or '').strip().lower() in {'sell', 'sld'} else 'buy'
    normalized_type = str(order_type or '').strip().lower().replace('-', '_')
    if normalized_type.startswith(('buy_', 'sell_')):
        return normalized_type.replace('_', '-', 1)
    if normalized_type.startswith(('buy-', 'sell-')):
        return normalized_type
    return f'{normalized_side}-{normalized_type}'


def _is_stop_order_type(order_type: Any) -> bool:
    value = str(order_type or '').strip().lower().replace('-', '_')
    return 'stop' in value


def _is_stop_limit_order_type(order_type: Any) -> bool:
    value = str(order_type or '').strip().lower().replace('-', '_')
    return 'stop_limit' in value


def _first_row(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response
    if isinstance(response, list):
        for item in response:
            if isinstance(item, dict):
                return item
    return {}


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _conid_from_topic(value: Any) -> str:
    topic = str(value or '').strip()
    if topic.startswith('smd+'):
        parts = topic.split('+', 2)
        if len(parts) >= 2:
            return parts[1]
    return ''


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _first_float(
    payload: dict[str, Any], keys: tuple[str, ...], default: float | None
) -> float | None:
    for key in keys:
        if key not in payload:
            continue
        value = _coerce_float(payload[key], None)
        if value is not None:
            return value
    return default


def _first_text(payload: dict[str, Any], keys: tuple[str, ...], default: str = '') -> str:
    for key in keys:
        value = payload.get(key)
        text = str(value or '').strip()
        if text:
            return text
    return default


def _normalize_position_row(row: dict[str, Any], asset_type: str) -> dict[str, Any]:
    payload = dict(row)
    symbol = _first_text(
        payload,
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
    )
    size = _first_float(payload, ('size', 'volume', 'position', 'qty', 'quantity'), 0.0) or 0.0
    entry_price = _first_float(
        payload,
        ('price', 'avg_price', 'average_price', 'avgCost', 'avgPrice', 'averageCost'),
        0.0,
    ) or 0.0
    current_price = _first_float(
        payload,
        (
            'current_price',
            'latest_price',
            'last_price',
            'marketPrice',
            'mktPrice',
            'markPrice',
            'market_price',
        ),
        None,
    )
    market_value = _first_float(
        payload,
        ('market_value', 'marketValue', 'mktValue', 'value'),
        None,
    )
    unrealized_pnl = _first_float(
        payload,
        (
            'unrealized_pnl',
            'unrealizedPNL',
            'UnrealizedPnL',
            'unrealizedPnl',
            'unrealizedpnl',
        ),
        None,
    )
    realized_pnl = _first_float(
        payload,
        ('realized_pnl', 'realizedPNL', 'RealizedPnL', 'realizedPnl', 'realizedpnl'),
        None,
    )
    sec_type = _first_text(payload, ('sec_type', 'secType', 'asset_type', 'assetClass'), asset_type)

    payload.update(
        {
            'data_name': symbol,
            'symbol': symbol,
            'instrument': symbol,
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
    if market_value is not None:
        payload['market_value'] = market_value
    if unrealized_pnl is not None:
        payload['unrealized_pnl'] = unrealized_pnl
        payload['gross_pnl'] = unrealized_pnl
    if realized_pnl is not None:
        payload['realized_pnl'] = realized_pnl
    return payload


def _coerce_float(value: Any, default: float | None) -> float | None:
    if isinstance(value, dict):
        for key in ('amount', 'value', 'balance', 'total'):
            if key in value:
                return _coerce_float(value[key], default)
    if value in (None, ''):
        return default
    if isinstance(value, str):
        value = value.strip().replace(',', '')
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_value(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ''):
            return value
    return None


def _first_contract_from_stock_search(symbol: str, response: Any) -> dict[str, Any]:
    if not isinstance(response, dict):
        return {}
    candidates: list[Any] = []
    if symbol in response:
        candidates.extend(response.get(symbol) or [])
    candidates.extend(value for value in response.values() if isinstance(value, dict))
    for entry in candidates:
        if not isinstance(entry, dict):
            continue
        contracts = entry.get('contracts')
        if isinstance(contracts, list):
            for contract in contracts:
                if isinstance(contract, dict):
                    merged = dict(entry)
                    merged.pop('contracts', None)
                    merged.update(contract)
                    merged.setdefault('symbol', symbol)
                    return merged
        if entry.get('conid') not in (None, ''):
            return dict(entry)
    return {}


def _first_contract_from_search(response: Any) -> dict[str, Any]:
    if isinstance(response, list):
        for item in response:
            if isinstance(item, dict):
                return dict(item)
    if isinstance(response, dict):
        contracts = response.get('contracts')
        if isinstance(contracts, list):
            for contract in contracts:
                if isinstance(contract, dict):
                    merged = dict(response)
                    merged.pop('contracts', None)
                    merged.update(contract)
                    return merged
        return dict(response)
    return {}


def _query_ib_contract_details(feed: Any, conid: Any) -> dict[str, Any]:
    getter = getattr(feed, '_get', None)
    if not callable(getter) or conid in (None, ''):
        return {}
    try:
        response = getter('/iserver/secdef/info', params={'conid': str(conid)})
    except Exception:
        return {}
    if isinstance(response, list):
        return _first_row(response)
    return _as_dict(response)


def _ib_symbol_spec(feed: Any, symbol: str, asset_type: str) -> dict[str, Any]:
    sec_type = _normalize_asset_type(asset_type)
    contract: dict[str, Any] = {}
    if sec_type == 'STK':
        search_stocks = getattr(feed, 'search_stocks', None)
        if callable(search_stocks):
            try:
                contract = _first_contract_from_stock_search(symbol, search_stocks(symbol))
            except Exception:
                contract = {}
    if not contract:
        search_contract = getattr(feed, 'search_contract', None)
        if callable(search_contract):
            try:
                contract = _first_contract_from_search(search_contract(symbol, sec_type))
            except Exception:
                contract = {}
    conid = _first_value(contract, ('conid', 'con_id', 'contract_id'))
    if conid in (None, ''):
        resolve = getattr(feed, 'resolve_conid', None)
        if callable(resolve):
            try:
                conid = resolve(symbol, sec_type)
            except Exception:
                conid = None
    details = _query_ib_contract_details(feed, conid)
    data = dict(contract)
    data.update(details)
    if conid not in (None, ''):
        data.setdefault('conid', conid)
    data.setdefault('symbol', symbol)
    data.setdefault('secType', sec_type)

    multiplier = _coerce_float(
        _first_value(
            data,
            (
                'multiplier',
                'contractMultiplier',
                'contract_multiplier',
                'contractSize',
                'contract_size',
            ),
        ),
        None,
    )
    if multiplier is None and sec_type == 'STK':
        multiplier = 1.0
    min_tick = _coerce_float(
        _first_value(data, ('minTick', 'min_tick', 'tick_size', 'price_tick')),
        None,
    )
    currency = _first_text(data, ('currency', 'Currency'), '')
    exchange = _first_text(data, ('exchange', 'listingExchange', 'validExchanges'), '')
    local_symbol = _first_text(data, ('localSymbol', 'local_symbol', 'contractDesc'), '')
    resolved_symbol = _first_text(data, ('symbol', 'ticker'), symbol)

    spec: dict[str, Any] = {
        'source': 'ib_web_gateway',
        'symbol': resolved_symbol,
        'data_name': resolved_symbol,
        'instrument': resolved_symbol,
        'localSymbol': local_symbol,
        'local_symbol': local_symbol,
        'conid': conid,
        'contract_id': conid,
        'secType': _first_text(data, ('secType', 'sec_type'), sec_type),
        'sec_type': _first_text(data, ('secType', 'sec_type'), sec_type),
        'asset_type': _first_text(data, ('secType', 'sec_type'), sec_type),
        'exchange': exchange,
        'exchange_id': exchange,
        'currency': currency,
        'price_tick': min_tick,
        'tick_size': min_tick,
        'multiplier': multiplier,
        'contract_multiplier': multiplier,
        'contract_size': multiplier,
        'last_trade_date': _first_value(
            data,
            ('lastTradingDay', 'lastTradeDateOrContractMonth', 'last_trade_date'),
        ),
    }
    return {key: value for key, value in spec.items() if value not in (None, '')}


__all__ = ['IbWebGatewayAdapter']
