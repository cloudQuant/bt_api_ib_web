from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

from bt_api_base.logging_factory import get_logger


def extract_cookie_string(cookie_str: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    if not cookie_str:
        return cookies
    for part in cookie_str.split(';'):
        item = part.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies


def get_cookies_from_browser(
    domain: str = 'localhost:5000', browser: str = 'chrome', path: str | None = None
) -> dict[str, str]:
    try:
        import browser_cookie3
    except ImportError:
        raise ImportError(
            'browser-cookie3 is required. Install: pip install browser-cookie3'
        ) from None

    logger = get_logger('ib_web_browser_cookies')
    domain_name = domain.split(':')[0]
    cookie_jar = None
    loaders = {
        'chrome': browser_cookie3.chrome,
        'firefox': browser_cookie3.firefox,
        'safari': browser_cookie3.safari,
        'edge': browser_cookie3.edge,
    }
    if browser.lower() in loaders:
        cookie_jar = loaders[browser.lower()](domain_name=domain_name)
    else:
        for loader in (browser_cookie3.chrome, browser_cookie3.firefox):
            try:
                cookie_jar = loader(domain_name=domain_name)
                if cookie_jar:
                    break
            except Exception as exc:
                logger.debug(
                    'Browser cookie extraction failed for %s: %s', loader.__name__, exc
                )
    if not cookie_jar:
        return {}
    cookies: dict[str, str] = {}
    for cookie in cookie_jar:
        if path and path not in cookie.path:
            continue
        cookies[str(cookie.name)] = str(cookie.value or '')
    return cookies


def get_cookies_from_file(file_path: str) -> dict[str, str]:
    path = Path(file_path).expanduser()
    if not path.exists():
        return {}
    try:
        with path.open(encoding='utf-8') as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict):
        return {str(key): str(value) for key, value in data.items()}
    if isinstance(data, list):
        return {
            str(item.get('name', item.get('key')) or ''): str(item.get('value') or '')
            for item in data
            if isinstance(item, dict)
        }
    return {}


def get_cookies_from_netscape(file_path: str) -> dict[str, str]:
    path = Path(file_path).expanduser()
    if not path.exists():
        return {}
    cookies: dict[str, str] = {}
    try:
        with path.open(encoding='utf-8') as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                parts = stripped.split('\t')
                if len(parts) >= 7:
                    cookies[parts[5]] = parts[6]
    except (OSError, UnicodeDecodeError):
        return {}
    return cookies


def get_ibkr_cookies(
    base_url: str = 'https://localhost:5000',
    cookie_source: str | None = None,
    browser: str = 'chrome',
    cookie_path: str = '/sso',
) -> dict[str, str]:
    if cookie_source is None or cookie_source == 'browser':
        return get_cookies_from_browser(
            domain=urlparse(base_url).netloc,
            browser=browser,
            path=cookie_path,
        )
    if cookie_source == 'env':
        return extract_cookie_string(os.environ.get('IB_WEB_COOKIES', ''))
    if cookie_source.startswith('file:'):
        file_path = cookie_source[5:]
        if file_path.endswith('.txt'):
            return get_cookies_from_netscape(file_path)
        return get_cookies_from_file(file_path)
    return extract_cookie_string(cookie_source)


def save_cookies_to_file(cookies: dict[str, str], file_path: str) -> None:
    path = Path(file_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        json.dump(cookies, handle, indent=2)
