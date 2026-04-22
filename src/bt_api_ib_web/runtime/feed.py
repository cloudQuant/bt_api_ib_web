from __future__ import annotations

import threading
import time
from typing import Any
from urllib.parse import urlparse

from bt_api_base.exceptions import RequestFailedError
from bt_api_base.feeds.capability import Capability
from bt_api_base.feeds.feed import Feed
from bt_api_base.feeds.http_client import HttpClient
from bt_api_base.logging_factory import get_logger

from bt_api_ib_web.exchange_data import IbWebExchangeDataFuture, IbWebExchangeDataStock
from bt_api_ib_web.runtime.browser_cookies import get_ibkr_cookies
from bt_api_ib_web.runtime.session import (
    ensure_authenticated_session,
    load_ib_web_settings,
)


class IbWebRequestData(Feed):
    def __init__(self, data_queue: Any = None, **kwargs: Any) -> None:
        super().__init__(data_queue)
        self.data_queue = data_queue
        auth_settings = load_ib_web_settings(
            overrides={
                'base_url': kwargs.get('base_url', 'https://localhost:5000'),
                'account_id': kwargs.get('account_id'),
                'verify_ssl': kwargs.get('verify_ssl', False),
                'timeout': kwargs.get('timeout', 10),
                'cookie_source': kwargs.get('cookie_source'),
                'cookie_browser': kwargs.get('cookie_browser', 'chrome'),
                'cookie_path': kwargs.get('cookie_path', '/sso'),
                'username': kwargs.get('username'),
                'password': kwargs.get('password'),
                'login_mode': kwargs.get('login_mode'),
                'login_browser': kwargs.get('login_browser'),
                'login_headless': kwargs.get('login_headless'),
                'login_timeout': kwargs.get('login_timeout'),
                'cookie_output': kwargs.get('cookie_output'),
            },
            base_dir=kwargs.get('cookie_base_dir') or None,
        )
        self.exchange_name = 'IB_WEB'
        self.base_url = str(auth_settings.get('base_url') or 'https://localhost:5000')
        self.account_id = kwargs.get('account_id') or auth_settings.get('account_id')
        self.access_token = kwargs.get('access_token')
        self.verify_ssl = auth_settings.get('verify_ssl', False)
        self.proxies = kwargs.get('proxies')
        self.timeout = auth_settings.get('timeout', 10)
        self.asset_type = kwargs.get('asset_type', 'STK')
        self._params = IbWebExchangeDataStock()
        self._params.rest_url = self.base_url
        self.request_logger = get_logger('ib_web_feed')
        self._http = HttpClient(
            venue='IB_WEB',
            timeout=self.timeout,
            verify=self.verify_ssl,
            proxies=self.proxies,
        )
        self._authenticated = False
        self._session_lock = threading.Lock()
        self._last_session_check = 0.0
        self._session_check_interval = 60.0
        self._subscribed_conids: set[int] = set()
        self._cookie_load_error: Exception | None = None
        self._last_connect_error: Exception | None = None
        self._cookies = kwargs.get('cookies')
        self._cookie_source = auth_settings.get('cookie_source')
        self._cookie_browser = auth_settings.get('cookie_browser', 'chrome')
        self._cookie_path = auth_settings.get('cookie_path', '/sso')
        self._cookie_output = auth_settings.get('cookie_output')
        self._cookie_base_dir = auth_settings.get('cookie_base_dir')
        self._username = auth_settings.get('username', '')
        self._password = auth_settings.get('password', '')
        self._login_mode = auth_settings.get('login_mode', 'paper')
        self._login_browser = auth_settings.get('login_browser', 'chrome')
        self._login_headless = auth_settings.get('login_headless', False)
        self._login_timeout = auth_settings.get('login_timeout', 180)
        self._allow_browser_login = bool(kwargs.get('allow_browser_login', False))
        self._loaded_cookies: dict[str, str] = {}
        self._load_cookies()

    @classmethod
    def _capabilities(cls) -> set[Capability]:
        return {
            Capability.GET_TICK,
            Capability.GET_DEPTH,
            Capability.GET_KLINE,
            Capability.MAKE_ORDER,
            Capability.CANCEL_ORDER,
            Capability.CANCEL_ALL,
            Capability.QUERY_ORDER,
            Capability.QUERY_OPEN_ORDERS,
            Capability.GET_DEALS,
            Capability.GET_BALANCE,
            Capability.GET_ACCOUNT,
            Capability.GET_POSITION,
            Capability.BATCH_ORDER,
        }

    def _build_headers(self) -> dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    def _is_local_base_url(self) -> bool:
        host = (urlparse(self.base_url).hostname or '').lower()
        return host in {'localhost', '127.0.0.1'}

    def _alternate_local_base_url(self) -> str:
        parsed = urlparse(self.base_url)
        target_scheme = (
            'http' if (parsed.scheme or 'https').lower() == 'https' else 'https'
        )
        return parsed._replace(scheme=target_scheme).geturl()

    def _rebuild_http_client(self) -> None:
        self._http.close()
        self._http = HttpClient(
            venue='IB_WEB',
            timeout=self.timeout,
            verify=self.verify_ssl,
            proxies=self.proxies,
        )

    def _maybe_switch_local_protocol(self, exc: RequestFailedError) -> bool:
        if not self._is_local_base_url():
            return False
        message = str(exc).lower()
        if 'ssl' not in message and 'wrong version number' not in message:
            return False
        alternate = self._alternate_local_base_url()
        if alternate == self.base_url:
            return False
        self.request_logger.warning(
            'IB Web request protocol fallback applied: %s -> %s after %s',
            self.base_url,
            alternate,
            exc,
        )
        self.base_url = alternate
        self._params.rest_url = alternate
        self._rebuild_http_client()
        return True

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: Any = None,
        **kwargs: Any,
    ) -> Any:
        headers = self._build_headers()
        request_cookies = dict(kwargs.pop('cookies', {}) or {})
        if self._loaded_cookies:
            request_cookies = {**self._loaded_cookies, **request_cookies}
        attempted_fallback = False
        while True:
            try:
                return self._http.request(
                    method=method,
                    url=f'{self.base_url}{endpoint}',
                    headers=headers,
                    params=params,
                    json_data=json_data,
                    cookies=request_cookies,
                    **kwargs,
                )
            except RequestFailedError as exc:
                if attempted_fallback or not self._maybe_switch_local_protocol(exc):
                    raise
                attempted_fallback = True

    def _get(
        self, endpoint: str, params: dict[str, Any] | None = None, **kwargs: Any
    ) -> Any:
        return self._request('GET', endpoint, params=params, **kwargs)

    def _post(self, endpoint: str, json_data: Any = None, **kwargs: Any) -> Any:
        return self._request('POST', endpoint, json_data=json_data, **kwargs)

    def _delete(self, endpoint: str, **kwargs: Any) -> Any:
        return self._request('DELETE', endpoint, **kwargs)

    def _load_cookies(self) -> None:
        self._cookie_load_error = None
        if self._cookies:
            self._loaded_cookies = dict(self._cookies)
            return
        if not self._cookie_source:
            self._loaded_cookies = {}
            return
        try:
            self._loaded_cookies = get_ibkr_cookies(
                base_url=self.base_url,
                cookie_source=self._cookie_source,
                browser=self._cookie_browser,
                cookie_path=self._cookie_path,
            )
        except Exception as exc:
            self._cookie_load_error = exc
            self._loaded_cookies = {}
            self.request_logger.warning('IB Web cookie load failed: %s', exc)

    def has_cookies(self) -> bool:
        return bool(self._loaded_cookies)

    def get_last_connect_error(self) -> Exception | None:
        return self._last_connect_error or self._cookie_load_error

    def _can_initialize_session(self) -> bool:
        return bool(self._allow_browser_login and self._username and self._password)

    def check_auth_status(self) -> Any:
        return self._post('/iserver/auth/status')

    def reauthenticate(self) -> Any:
        return self._post('/iserver/reauthenticate')

    def _update_auth_state(self) -> bool:
        result = self.check_auth_status()
        self._authenticated = bool(
            result.get('authenticated', False) or result.get('connected', False)
        )
        return self._authenticated

    def _initialize_authenticated_session(self) -> dict[str, Any]:
        session = ensure_authenticated_session(
            overrides={
                'base_url': self.base_url,
                'account_id': self.account_id or '',
                'verify_ssl': self.verify_ssl,
                'timeout': int(float(self.timeout)),
                'cookie_source': self._cookie_source or '',
                'cookie_browser': self._cookie_browser,
                'cookie_path': self._cookie_path,
                'username': self._username,
                'password': self._password,
                'login_mode': self._login_mode,
                'login_browser': self._login_browser,
                'login_headless': self._login_headless,
                'login_timeout': self._login_timeout,
                'cookie_output': self._cookie_output or '',
            },
            base_dir=self._cookie_base_dir or None,
        )
        self._loaded_cookies = dict(session.get('cookies') or {})
        cookie_output = session.get('cookie_output')
        if cookie_output:
            self._cookie_source = f'file:{cookie_output}'
            self._cookie_output = cookie_output
        account_id = str(session.get('account_id') or '').strip()
        if account_id:
            self.account_id = account_id
        return session

    def connect(self) -> None:
        self._last_connect_error = None
        self._load_cookies()
        last_error: Exception | None = None
        for attempt in ('existing', 'initialize'):
            if attempt == 'initialize':
                if not self._can_initialize_session():
                    break
                try:
                    self._initialize_authenticated_session()
                except Exception as exc:
                    last_error = exc
                    break
            try:
                if self._update_auth_state():
                    return
                self.reauthenticate()
                if self._update_auth_state():
                    return
                last_error = RuntimeError('IB Web authentication failed')
            except Exception as exc:
                last_error = exc
            if attempt == 'existing' and not self._can_initialize_session():
                break
        self._authenticated = False
        self._last_connect_error = last_error or RuntimeError(
            'IB Web authentication failed'
        )
        if self._last_connect_error:
            self.request_logger.warning(
                'IB Web connect failed: %s', self._last_connect_error
            )

    def disconnect(self) -> None:
        self._authenticated = False
        self._http.close()

    def is_connected(self) -> bool:
        return self._authenticated

    def _ensure_session(self) -> None:
        now = time.time()
        if now - self._last_session_check <= self._session_check_interval:
            return
        with self._session_lock:
            if now - self._last_session_check <= self._session_check_interval:
                return
            try:
                self._authenticated = self._update_auth_state()
                if not self._authenticated:
                    self.connect()
            except Exception as exc:
                self.request_logger.warning('Session check failed: %s', exc)
            self._last_session_check = now

    def search_stocks(self, symbols: str, extra_data: Any = None, **kwargs: Any) -> Any:
        return self._get('/trsrv/stocks', params={'symbols': symbols})

    def search_contract(
        self, symbol: str, sec_type: str = 'STK', extra_data: Any = None, **kwargs: Any
    ) -> Any:
        return self._get(
            '/iserver/secdef/search', params={'symbol': symbol, 'secType': sec_type}
        )

    def resolve_conid(self, symbol: str, sec_type: str = 'STK') -> Any:
        if sec_type == 'STK':
            response = self.search_stocks(symbol)
            if symbol in response:
                entries = response[symbol]
                if entries and isinstance(entries, list):
                    contracts = entries[0].get('contracts', [])
                    if contracts:
                        return contracts[0].get('conid')
        else:
            response = self.search_contract(symbol, sec_type)
            if response and isinstance(response, list):
                return response[0].get('conid')
        return None

    def get_tick(self, symbol: Any, extra_data: Any = None, **kwargs: Any) -> Any:
        conid = self._resolve_conid_param(symbol, extra_data)
        field_str = ','.join(
            str(item)
            for item in kwargs.get('fields', self._params.default_snapshot_fields)
        )
        params = {'conids': str(conid), 'fields': field_str}
        self._get('/iserver/marketdata/snapshot', params=params)
        time.sleep(0.5)
        response = self._get('/iserver/marketdata/snapshot', params=params)
        if isinstance(response, list) and response:
            return response[0]
        return response

    def get_depth(
        self, symbol: Any, count: int = 5, extra_data: Any = None, **kwargs: Any
    ) -> Any:
        return self.get_tick(
            symbol, extra_data=extra_data, fields=['84', '85', '86', '88'], **kwargs
        )

    def get_kline(
        self,
        symbol: Any,
        period: str,
        count: int = 100,
        extra_data: Any = None,
        **kwargs: Any,
    ) -> Any:
        conid = self._resolve_conid_param(symbol, extra_data)
        params = {
            'conid': str(conid),
            'period': self._params.kline_periods.get(period, period),
            'bar': str(count or 100),
        }
        start_time = kwargs.get('start_time')
        if start_time:
            params['startTime'] = str(start_time)
        return self._get('/iserver/marketdata/history', params=params)

    def _handle_order_reply(self, response: Any) -> Any:
        if isinstance(response, list) and response:
            first = response[0]
            if isinstance(first, dict) and 'id' in first and 'message' in first:
                return self._post(
                    f'/iserver/reply/{first["id"]}', json_data={'confirmed': True}
                )
        return response

    def _get_account_id(self, extra_data: Any = None) -> str:
        if isinstance(extra_data, dict) and extra_data.get('account_id'):
            return str(extra_data['account_id'])
        if self.account_id:
            return str(self.account_id)
        raise ValueError('account_id is required.')

    def make_order(
        self,
        symbol: Any,
        volume: Any,
        price: Any,
        order_type: str = 'buy-limit',
        offset: str = 'open',
        post_only: bool = False,
        client_order_id: str | None = None,
        extra_data: Any = None,
        **kwargs: Any,
    ) -> Any:
        conid = self._resolve_conid_param(symbol, extra_data)
        account_id = self._get_account_id(extra_data)
        side, ib_order_type = self._parse_order_type(order_type)
        tif = extra_data.get('tif', 'DAY') if isinstance(extra_data, dict) else 'DAY'
        order = {
            'conid': conid,
            'side': side,
            'orderType': ib_order_type,
            'quantity': volume,
            'tif': tif,
        }
        if ib_order_type in {'LMT', 'STP_LMT'} and price not in (None, ''):
            order['price'] = price
        if (
            ib_order_type in {'STP', 'STP_LMT'}
            and isinstance(extra_data, dict)
            and extra_data.get('aux_price')
        ):
            order['auxPrice'] = extra_data['aux_price']
        if client_order_id:
            order['cOID'] = client_order_id
        response = self._post(
            f'/iserver/account/{account_id}/orders',
            json_data={'orders': [order]},
        )
        return self._handle_order_reply(response)

    def cancel_order(
        self, symbol: Any, order_id: Any, extra_data: Any = None, **kwargs: Any
    ) -> Any:
        return self._delete(
            f'/iserver/account/{self._get_account_id(extra_data)}/order/{order_id}'
        )

    def get_open_orders(
        self, symbol: Any = None, extra_data: Any = None, **kwargs: Any
    ) -> Any:
        params: dict[str, Any] = {'force': 'true'}
        if self.account_id:
            params['accountId'] = self.account_id
        if isinstance(extra_data, dict) and 'filters' in extra_data:
            params['filters'] = extra_data['filters']
        return self._get('/iserver/account/orders', params=params)

    def get_position(
        self, symbol: Any = None, extra_data: Any = None, **kwargs: Any
    ) -> Any:
        account_id = self._get_account_id(extra_data)
        if self.has_cookies():
            try:
                return self._get(
                    f'/portfolio/{account_id}/positions/{kwargs.get("page_id", 0)}'
                )
            except Exception as exc:
                self.request_logger.debug(
                    'Portfolio positions endpoint failed, falling back: %s', exc
                )
        raise NotImplementedError(
            'get_position requires browser session authentication. '
            'Please set IB_WEB_COOKIE_SOURCE=browser or use a cookie file.'
        )

    def get_account(
        self, symbol: str = 'ALL', extra_data: Any = None, **kwargs: Any
    ) -> Any:
        return self._get(f'/iserver/account/{self._get_account_id(extra_data)}/summary')

    def get_balance(
        self, symbol: Any = None, extra_data: Any = None, **kwargs: Any
    ) -> Any:
        return self._get(f'/iserver/account/{self._get_account_id(extra_data)}/summary')

    def get_deals(
        self,
        symbol: Any = None,
        count: int = 100,
        start_time: Any = None,
        end_time: Any = None,
        extra_data: Any = None,
        **kwargs: Any,
    ) -> Any:
        return self._get('/iserver/account/trades')

    def _resolve_conid_param(self, symbol: Any, extra_data: Any = None) -> Any:
        if isinstance(symbol, int):
            return symbol
        if isinstance(extra_data, dict) and 'conid' in extra_data:
            return extra_data['conid']
        try:
            return int(symbol)
        except (TypeError, ValueError):
            pass
        conid = self.resolve_conid(str(symbol), self.asset_type)
        if conid is None:
            raise ValueError(f'Cannot resolve conid for symbol: {symbol}')
        return conid

    def _parse_order_type(self, order_type: str) -> tuple[str, str]:
        value = order_type.lower()
        side = (
            'BUY'
            if value.startswith('buy')
            else 'SELL'
            if value.startswith('sell')
            else 'BUY'
        )
        if 'market' in value:
            ib_type = 'MKT'
        elif 'stop_limit' in value or 'stop-limit' in value:
            ib_type = 'STP_LMT'
        elif 'stop' in value:
            ib_type = 'STP'
        elif 'limit' in value:
            ib_type = 'LMT'
        else:
            ib_type = self._params.order_type_map.get(value, value.upper())
        return side, ib_type


class IbWebRequestDataStock(IbWebRequestData):
    def __init__(self, data_queue: Any = None, **kwargs: Any) -> None:
        super().__init__(data_queue, **kwargs)
        self.asset_type = kwargs.get('asset_type', 'STK')
        self._params = IbWebExchangeDataStock()
        self._params.rest_url = self.base_url


class IbWebRequestDataFuture(IbWebRequestData):
    def __init__(self, data_queue: Any = None, **kwargs: Any) -> None:
        super().__init__(data_queue, **kwargs)
        self.asset_type = kwargs.get('asset_type', 'FUT')
        self._params = IbWebExchangeDataFuture()
        self._params.rest_url = self.base_url
