from __future__ import annotations

import contextlib
import json
import threading
import time
from typing import Any
from urllib.parse import urlparse

from bt_api_ib_web.runtime.base_stream import BaseDataStream, ConnectionState


def _is_local_base_url(base_url: str) -> bool:
    host = (urlparse(str(base_url or "")).hostname or "").lower()
    return host in {"localhost", "127.0.0.1"}


def _normalize_ws_message(message: Any) -> str:
    if isinstance(message, (bytes, bytearray)):
        return bytes(message).decode("utf-8", errors="replace")
    return str(message)


class IbWebDataStream(BaseDataStream):
    def __init__(self, data_queue: Any = None, **kwargs: Any) -> None:
        super().__init__(data_queue, **kwargs)
        self.base_url = kwargs.get("base_url", "https://localhost:5000")
        self.verify_ssl = kwargs.get("verify_ssl", False)
        self.topics = kwargs.get("topics", [])
        self._ws: Any = None
        self._heartbeat_interval = 30
        self._heartbeat_thread: threading.Thread | None = None
        self._ws_thread: threading.Thread | None = None
        self._reconnect_delay = 5
        self._max_reconnect_delay = 60
        self._subscribed_conids: set[int] = set()

    def _build_ws_url(self) -> str:
        base = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
        return f"{base}/ws" if "/v1/api" in base else f"{base}/v1/api/ws"

    def connect(self) -> None:
        try:
            import websocket
        except ImportError:
            raise ImportError(
                "websocket-client required. Install: pip install websocket-client"
            ) from None
        self.state = ConnectionState.CONNECTING
        ssl_opts: dict[str, Any] = {}
        if not self.verify_ssl:
            import ssl

            ssl_opts = {"cert_reqs": ssl.CERT_NONE, "check_hostname": False}
        self._ws = websocket.WebSocketApp(
            self._build_ws_url(),
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self._ws_thread = threading.Thread(
            target=self._ws.run_forever,
            kwargs={
                **({"sslopt": ssl_opts} if ssl_opts else {}),
                **(
                    {"http_no_proxy": ["localhost", "127.0.0.1"]}
                    if _is_local_base_url(self.base_url)
                    else {}
                ),
            },
            daemon=True,
        )
        self._ws_thread.start()

    def disconnect(self) -> None:
        self._running = False
        if self._ws:
            with contextlib.suppress(Exception):
                self._ws.close()
        self.state = ConnectionState.DISCONNECTED

    def subscribe_topics(self, topics: list[dict[str, Any]]) -> None:
        for topic in topics:
            if topic.get("topic") == "market_data" and topic.get("conid"):
                self._subscribe_market_data(
                    topic["conid"], topic.get("fields", ["31", "84", "85", "86", "88"])
                )

    def _subscribe_market_data(
        self, conid: Any, fields: list[str] | None = None
    ) -> None:
        payload = json.dumps({"fields": fields or ["31", "84", "85", "86", "88"]})
        msg = f"smd+{conid}+{payload}"
        if self._ws and self._running:
            try:
                self._ws.send(msg)
                self._subscribed_conids.add(int(conid))
            except Exception as exc:
                self.logger.warning("Subscribe failed for conid=%s: %s", conid, exc)

    def _on_open(self, ws: Any) -> None:
        self.state = ConnectionState.CONNECTED
        self._start_heartbeat()
        if self.topics:
            self.subscribe_topics(self.topics)

    def _on_message(self, ws: Any, message: Any) -> None:
        try:
            text = _normalize_ws_message(message)
            if text.startswith("{") or text.startswith("["):
                self._process_message(json.loads(text))
        except json.JSONDecodeError:
            return
        except Exception as exc:
            self.logger.warning("WS message processing error: %s", exc)

    def _process_message(self, data: Any) -> None:
        if not isinstance(data, dict):
            return
        if (
            "conid" in data
            or "conidEx" in data
            or str(data.get("topic", "")).startswith("smd")
        ):
            self.push_data({"type": "market_data", "exchange": "IB_WEB", "data": data})
        elif str(data.get("topic", "")).startswith("sor"):
            self.push_data({"type": "order_update", "exchange": "IB_WEB", "data": data})
        elif str(data.get("topic", "")).startswith("spl"):
            self.push_data({"type": "pnl_update", "exchange": "IB_WEB", "data": data})
        else:
            self.push_data({"type": "system", "exchange": "IB_WEB", "data": data})

    def _on_error(self, ws: Any, error: Any) -> None:
        self.logger.warning("IB WebSocket error: %s", error)
        self.state = ConnectionState.ERROR

    def _on_close(self, ws: Any, close_status_code: Any, close_msg: Any) -> None:
        self.state = ConnectionState.DISCONNECTED
        if self._running:
            time.sleep(self._reconnect_delay)
            self._reconnect_delay = min(
                self._reconnect_delay * 2, self._max_reconnect_delay
            )
            try:
                self.connect()
                for conid in list(self._subscribed_conids):
                    self._subscribe_market_data(conid)
            except Exception as exc:
                self.logger.warning("Reconnect failed: %s", exc)

    def _start_heartbeat(self) -> None:
        def heartbeat_loop() -> None:
            while self._running and self._ws:
                try:
                    self._ws.send("tic")
                except Exception:
                    break
                time.sleep(self._heartbeat_interval)

        self._heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def _run_loop(self) -> None:
        self.connect()
        while self._running:
            time.sleep(1)


class IbWebAccountStream(BaseDataStream):
    def __init__(self, data_queue: Any = None, **kwargs: Any) -> None:
        super().__init__(data_queue, **kwargs)
        self.base_url = kwargs.get("base_url", "https://localhost:5000")
        self.verify_ssl = kwargs.get("verify_ssl", False)
        self.account_id = kwargs.get("account_id")
        self.topics = kwargs.get("topics", [])
        self._ws: Any = None
        self._heartbeat_interval = 30
        self._reconnect_delay = 5
        self._max_reconnect_delay = 60
        self._ws_thread: threading.Thread | None = None

    def _build_ws_url(self) -> str:
        base = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
        return f"{base}/ws" if "/v1/api" in base else f"{base}/v1/api/ws"

    def connect(self) -> None:
        try:
            import websocket
        except ImportError:
            raise ImportError(
                "websocket-client required. Install: pip install websocket-client"
            ) from None
        self.state = ConnectionState.CONNECTING
        ssl_opts: dict[str, Any] = {}
        if not self.verify_ssl:
            import ssl

            ssl_opts = {"cert_reqs": ssl.CERT_NONE, "check_hostname": False}
        self._ws = websocket.WebSocketApp(
            self._build_ws_url(),
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self._ws_thread = threading.Thread(
            target=self._ws.run_forever,
            kwargs={
                **({"sslopt": ssl_opts} if ssl_opts else {}),
                **(
                    {"http_no_proxy": ["localhost", "127.0.0.1"]}
                    if _is_local_base_url(self.base_url)
                    else {}
                ),
            },
            daemon=True,
        )
        self._ws_thread.start()

    def disconnect(self) -> None:
        self._running = False
        if self._ws:
            with contextlib.suppress(Exception):
                self._ws.close()
        self.state = ConnectionState.DISCONNECTED

    def subscribe_topics(self, topics: list[dict[str, Any]]) -> None:
        for topic in topics:
            topic_type = topic.get("topic", "")
            if topic_type == "account":
                self._send_ws("sacct")
            elif topic_type == "order":
                self._send_ws("sor")
            elif topic_type == "pnl":
                self._send_ws(f"spl+{self.account_id}" if self.account_id else "spl")
            elif topic_type == "trade":
                self._send_ws("str")

    def _send_ws(self, msg: str) -> None:
        if self._ws and self._running:
            try:
                self._ws.send(msg)
            except Exception as exc:
                self.logger.warning("WS send failed: %s", exc)

    def _on_open(self, ws: Any) -> None:
        self.state = ConnectionState.CONNECTED
        self._start_heartbeat()
        if self.topics:
            self.subscribe_topics(self.topics)

    def _on_message(self, ws: Any, message: Any) -> None:
        try:
            text = _normalize_ws_message(message)
            if text.startswith("{") or text.startswith("["):
                self._process_message(json.loads(text))
        except json.JSONDecodeError:
            return
        except Exception as exc:
            self.logger.warning("Account WS message error: %s", exc)

    def _process_message(self, data: Any) -> None:
        if not isinstance(data, dict):
            return
        topic = str(data.get("topic", ""))
        if topic.startswith("spl"):
            payload_type = "pnl_update"
        elif topic.startswith("sor"):
            payload_type = "order_update"
        elif topic.startswith("sacct") or "accountId" in data:
            payload_type = "account_update"
        elif topic.startswith("str"):
            payload_type = "trade_update"
        else:
            payload_type = "account_system"
        self.push_data({"type": payload_type, "exchange": "IB_WEB", "data": data})

    def _on_error(self, ws: Any, error: Any) -> None:
        self.logger.warning("IB Account WebSocket error: %s", error)
        self.state = ConnectionState.ERROR

    def _on_close(self, ws: Any, close_status_code: Any, close_msg: Any) -> None:
        self.state = ConnectionState.DISCONNECTED
        if self._running:
            time.sleep(self._reconnect_delay)
            self._reconnect_delay = min(
                self._reconnect_delay * 2, self._max_reconnect_delay
            )
            try:
                self.connect()
            except Exception as exc:
                self.logger.warning("Account WS reconnect failed: %s", exc)

    def _start_heartbeat(self) -> None:
        def heartbeat_loop() -> None:
            while self._running and self._ws:
                try:
                    self._ws.send("tic")
                except Exception:
                    break
                time.sleep(self._heartbeat_interval)

        threading.Thread(target=heartbeat_loop, daemon=True).start()

    def _run_loop(self) -> None:
        self.connect()
        while self._running:
            time.sleep(1)
