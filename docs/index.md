# Interactive Brokers Web API Documentation

## English

Welcome to the Interactive Brokers Web API documentation for bt_api.

### Overview

`bt_api_ib_web` provides an `IbWebGatewayAdapter` for the [bt_api](https://github.com/cloudQuant/bt_api_py) framework. It connects to Interactive Brokers Web API via WebSocket and REST, supporting stock and futures trading.

### IbWebGatewayAdapter

The main adapter class. Import it from the package root:

```python
from bt_api_ib_web import IbWebGatewayAdapter
```

#### Constructor

```python
IbWebGatewayAdapter(
    base_url="https://localhost:5000",  # IB Web API endpoint
    asset_type="STK",                    # "STK" (stock) or "FUT" (future)
    gateway_startup_timeout_sec=10.0,    # Connection timeout in seconds
    **kwargs                            # Additional parameters passed to feeds
)
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|--------|-------------|
| `connect()` | — | `None` | Connect to IB Web API and start background threads |
| `disconnect()` | — | `None` | Stop threads and close connections |
| `subscribe_symbols()` | `symbols: list[str]` | `dict` | Subscribe to one or more symbols by conId or alias |
| `get_balance()` | — | `dict` | Retrieve account balance and cash |
| `get_positions()` | — | `list[dict]` | List all open positions |
| `place_order()` | `payload: dict` | `dict` | Place an order; see payload format below |
| `cancel_order()` | `payload: dict` | `dict` | Cancel an order by ID |

#### Order Payload Format

```python
{
    "symbol": "AAPL",          # Symbol name or conId
    "size": 10,               # Order size (volume)
    "price": 150.0,          # Limit price; omit or None for market orders
    "order_type": "limit",    # Order type: "market", "limit", "stop", etc.
    "side": "buy",            # "buy" or "sell"
    "client_order_id": "ref", # Optional: client-side order reference
    "extra_data": {},         # Optional: extra IB-specific parameters
}
```

#### Balance Response Format

```python
{
    "cash": 10000.0,          # Cash balance
    "value": 50000.0,        # Total portfolio value
    "raw": {...}             # Raw response from IB API
}
```

#### Subscribe Symbols

Pass a list of conIds or symbol aliases. The adapter resolves them and subscribes to market data via WebSocket:

```python
adapter.subscribe_symbols(["265598", "AAPL", "ES"])
```

### Installation

```bash
pip install bt_api_ib_web
```

### Architecture

```
bt_api_ib_web/
├── src/bt_api_ib_web/
│   ├── gateway/adapter.py        # IbWebGatewayAdapter
│   ├── runtime/feed.py          # IbWebRequestDataStock / Future
│   ├── runtime/stream.py         # IbWebDataStream / IbWebAccountStream
│   └── containers/              # Data containers
├── tests/
└── docs/
```

---

## 中文

欢迎使用 bt_api 的 Interactive Brokers Web API 文档。

### 概述

`bt_api_ib_web` 为 [bt_api](https://github.com/cloudQuant/bt_api_py) 框架提供 `IbWebGatewayAdapter`，通过 WebSocket 和 REST 连接盈透证券 Web API，支持股票和期货交易。

### IbWebGatewayAdapter

主适配器类，从包根目录导入：

```python
from bt_api_ib_web import IbWebGatewayAdapter
```

#### 构造函数

```python
IbWebGatewayAdapter(
    base_url="https://localhost:5000",  # IB Web API 端点
    asset_type="STK",                    # "STK"（股票）或 "FUT"（期货）
    gateway_startup_timeout_sec=10.0,    # 连接超时时间（秒）
    **kwargs                            # 传递给 feed 的额外参数
)
```

#### 方法一览

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `connect()` | — | `None` | 连接 IB Web API 并启动后台线程 |
| `disconnect()` | — | `None` | 停止线程并关闭连接 |
| `subscribe_symbols()` | `symbols: list[str]` | `dict` | 按 conId 或别名订阅一个或多个品种 |
| `get_balance()` | — | `dict` | 获取账户余额和现金 |
| `get_positions()` | — | `list[dict]` | 列出所有持仓 |
| `place_order()` | `payload: dict` | `dict` | 下单；详见 payload 格式 |
| `cancel_order()` | `payload: dict` | `dict` | 按 ID 撤单 |

#### 下单 Payload 格式

```python
{
    "symbol": "AAPL",          # 品种名或 conId
    "size": 10,               # 委托数量
    "price": 150.0,           # 限价；市价单不填或填 None
    "order_type": "limit",    # 订单类型："market"、"limit"、"stop" 等
    "side": "buy",            # "buy" 或 "sell"
    "client_order_id": "ref", # 可选：客户端订单引用
    "extra_data": {},         # 可选：额外 IB 参数
}
```

#### 余额返回格式

```python
{
    "cash": 10000.0,          # 现金余额
    "value": 50000.0,        # 账户总价值
    "raw": {...}             # IB API 原始响应
}
```

#### 订阅品种

传入 conId 或品种别名列表。适配器解析后通过 WebSocket 订阅行情：

```python
adapter.subscribe_symbols(["265598", "AAPL", "ES"])
```

### 安装

```bash
pip install bt_api_ib_web
```

### 架构

```
bt_api_ib_web/
├── src/bt_api_ib_web/
│   ├── gateway/adapter.py        # IbWebGatewayAdapter
│   ├── runtime/feed.py           # IbWebRequestDataStock / Future
│   ├── runtime/stream.py         # IbWebDataStream / IbWebAccountStream
│   └── containers/              # 数据容器
├── tests/
└── docs/
```

---

## Online Documentation

| Resource | Link |
|----------|------|
| English Docs | https://bt-api-ib-web.readthedocs.io/ |
| Chinese Docs | https://bt-api-ib-web.readthedocs.io/zh/latest/ |
| GitHub Repository | https://github.com/cloudQuant/bt_api_ib_web |
| Issue Tracker | https://github.com/cloudQuant/bt_api_ib_web/issues |
