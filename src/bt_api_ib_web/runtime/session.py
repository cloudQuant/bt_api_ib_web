from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
import urllib3
from dotenv import dotenv_values

from bt_api_ib_web.runtime.browser_cookies import get_ibkr_cookies, save_cookies_to_file

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_local_path(
    path_value: str | Path, base_dir: str | Path | None = None
) -> Path:
    raw_path = Path(path_value).expanduser()
    if raw_path.is_absolute():
        return raw_path
    base_path = Path(base_dir).expanduser() if base_dir else project_root()
    return (base_path / raw_path).resolve()


def to_relative_path(path_value: str | Path, base_dir: str | Path | None = None) -> str:
    target = resolve_local_path(path_value, base_dir=base_dir)
    root = (
        Path(base_dir).expanduser().resolve() if base_dir else project_root().resolve()
    )
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        return os.path.relpath(target, root).replace('\\', '/')


def normalize_cookie_source(
    cookie_source: str | None, base_dir: str | Path | None = None
) -> str:
    value = str(cookie_source or '').strip()
    if not value or value in {'browser', 'env'} or (';' in value and '=' in value):
        return value
    path_value = value[5:] if value.startswith('file:') else value
    return f'file:{resolve_local_path(path_value, base_dir=base_dir)}'


def default_cookie_output(base_dir: str | Path | None = None) -> Path:
    return resolve_local_path(Path('configs') / 'ibkr_cookies.json', base_dir=base_dir)


def load_ib_web_settings(
    overrides: dict[str, Any] | None = None,
    base_dir: str | Path | None = None,
    env_file: str | Path | None = None,
) -> dict[str, Any]:
    env_path = (
        resolve_local_path(env_file, base_dir=base_dir)
        if env_file
        else project_root() / '.env'
    )
    env_values = dotenv_values(env_path)
    data = dict(overrides or {})

    def pick(name: str, default: Any = '') -> Any:
        value = data.get(name)
        if value not in (None, ''):
            return value
        env_value = os.environ.get(name)
        if env_value not in (None, ''):
            return env_value
        file_value = env_values.get(name)
        if file_value not in (None, ''):
            return file_value
        return default

    def pick_bool(name: str, default: bool = False) -> bool:
        value = pick(name, default)
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}

    def pick_int(name: str, default: int) -> int:
        try:
            return int(pick(name, default))
        except (TypeError, ValueError):
            return default

    resolved_base_dir = Path(base_dir).expanduser() if base_dir else project_root()
    cookie_output_value = str(
        pick('cookie_output', pick('IB_WEB_COOKIE_OUTPUT', '')) or ''
    ).strip()
    cookie_source_value = str(
        pick('cookie_source', pick('IB_WEB_COOKIE_SOURCE', '')) or ''
    ).strip()
    cookie_output_path = (
        resolve_local_path(cookie_output_value, base_dir=resolved_base_dir)
        if cookie_output_value
        else default_cookie_output(base_dir=resolved_base_dir)
    )
    return {
        'base_url': str(
            pick('base_url', pick('IB_WEB_BASE_URL', 'https://localhost:5000'))
        ).strip(),
        'account_id': str(pick('account_id', pick('IB_WEB_ACCOUNT_ID', ''))).strip(),
        'verify_ssl': pick_bool('verify_ssl', pick_bool('IB_WEB_VERIFY_SSL', False)),
        'timeout': pick_int('timeout', pick_int('IB_WEB_TIMEOUT', 10)),
        'cookie_source': normalize_cookie_source(
            cookie_source_value, base_dir=resolved_base_dir
        ),
        'cookie_browser': str(
            pick('cookie_browser', pick('IB_WEB_COOKIE_BROWSER', 'chrome'))
        ).strip()
        or 'chrome',
        'cookie_path': str(
            pick('cookie_path', pick('IB_WEB_COOKIE_PATH', '/sso'))
        ).strip()
        or '/sso',
        'username': str(pick('username', pick('IB_WEB_USERNAME', ''))).strip(),
        'password': str(pick('password', pick('IB_WEB_PASSWORD', ''))).strip(),
        'login_mode': str(pick('login_mode', pick('IB_WEB_LOGIN_MODE', 'paper')))
        .strip()
        .lower()
        or 'paper',
        'login_browser': str(
            pick('login_browser', pick('IB_WEB_LOGIN_BROWSER', 'chrome'))
        ).strip()
        or 'chrome',
        'login_headless': pick_bool(
            'login_headless', pick_bool('IB_WEB_LOGIN_HEADLESS', False)
        ),
        'login_timeout': pick_int(
            'login_timeout', pick_int('IB_WEB_LOGIN_TIMEOUT', 180)
        ),
        'cookie_output': str(cookie_output_path),
        'cookie_output_relative': to_relative_path(
            cookie_output_path, base_dir=resolved_base_dir
        ),
        'cookie_base_dir': str(resolved_base_dir),
        'env_file': str(env_path),
    }


def api_base_url(base_url: str) -> str:
    value = str(base_url or '').rstrip('/')
    if value.endswith('/v1/api'):
        return value
    return value + '/v1/api'


def auth_status(
    base_url: str, cookies: dict[str, str], verify_ssl: bool = False, timeout: int = 10
) -> requests.Response:
    return requests.post(
        f'{api_base_url(base_url)}/iserver/auth/status',
        cookies=cookies,
        verify=verify_ssl,
        timeout=timeout,
    )


def auth_response_is_authenticated(response: requests.Response) -> bool:
    if response.status_code != 200:
        return False
    try:
        payload = response.json()
    except ValueError:
        return False
    if not isinstance(payload, dict):
        return False
    return bool(payload.get('authenticated', False) or payload.get('connected', False))


def fetch_accounts(
    base_url: str, cookies: dict[str, str], verify_ssl: bool = False, timeout: int = 10
) -> list[dict[str, Any]]:
    response = requests.get(
        f'{api_base_url(base_url)}/portfolio/accounts',
        cookies=cookies,
        verify=verify_ssl,
        timeout=timeout,
    )
    if response.status_code != 200:
        return []
    payload = response.json()
    return payload if isinstance(payload, list) else []


def pick_account_id(accounts: list[dict[str, Any]], login_mode: str) -> str:
    if login_mode == 'paper':
        for account in accounts:
            for key in ('accountId', 'id', 'accountIdKey'):
                value = str(account.get(key) or '')
                if value.upper().startswith('DU'):
                    return value
    for account in accounts:
        for key in ('accountId', 'id', 'accountIdKey'):
            value = str(account.get(key) or '')
            if value:
                return value
    return ''


def current_cookie_payload(settings: dict[str, Any]) -> dict[str, str]:
    source = str(settings.get('cookie_source') or '')
    if not source:
        return {}
    return get_ibkr_cookies(
        base_url=str(settings.get('base_url') or 'https://localhost:5000'),
        cookie_source=source,
        browser=str(settings.get('cookie_browser') or 'chrome'),
        cookie_path=str(settings.get('cookie_path') or '/sso'),
    )


def cookies_are_authenticated(
    settings: dict[str, Any], cookies: dict[str, str]
) -> bool:
    if not cookies:
        return False
    try:
        response = auth_status(
            str(settings.get('base_url') or 'https://localhost:5000'),
            cookies,
            verify_ssl=bool(settings.get('verify_ssl', False)),
            timeout=int(settings.get('timeout', 10)),
        )
    except requests.RequestException:
        return False
    return auth_response_is_authenticated(response)


def ensure_authenticated_session(
    overrides: dict[str, Any] | None = None,
    base_dir: str | Path | None = None,
    env_file: str | Path | None = None,
) -> dict[str, Any]:
    settings = load_ib_web_settings(
        overrides=overrides, base_dir=base_dir, env_file=env_file
    )
    cookies = current_cookie_payload(settings)
    if not cookies or not cookies_are_authenticated(settings, cookies):
        raise RuntimeError(
            'IB Web session is not authenticated. Provide valid IB_WEB_COOKIE_SOURCE/IB_WEB_COOKIES.'
        )
    account_id = str(settings.get('account_id') or '')
    if not account_id:
        accounts = fetch_accounts(
            str(settings.get('base_url') or 'https://localhost:5000'),
            cookies,
            verify_ssl=bool(settings.get('verify_ssl', False)),
            timeout=int(settings.get('timeout', 10)),
        )
        account_id = pick_account_id(
            accounts, str(settings.get('login_mode') or 'paper')
        )
    cookie_output = str(
        settings.get('cookie_output')
        or default_cookie_output(base_dir=settings.get('cookie_base_dir'))
    )
    save_cookies_to_file(cookies, cookie_output)
    return {
        'cookies': cookies,
        'cookie_output': cookie_output,
        'cookie_output_relative': str(settings.get('cookie_output_relative') or ''),
        'cookie_source': normalize_cookie_source(
            f'file:{cookie_output}', base_dir=settings.get('cookie_base_dir')
        ),
        'account_id': account_id,
        'status_code': 200,
        'used_login': False,
    }
