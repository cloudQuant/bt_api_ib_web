# Interactive Brokers Web API

Interactive Brokers Web API plugin for bt_api, supporting stock and futures trading via IB Web API.

[![PyPI Version](https://img.shields.io/pypi/v/bt_api_ib_web.svg)](https://pypi.org/project/bt_api_ib_web/)
[![Python Versions](https://img.shields.io/pypi/pyversions/bt_api_ib_web.svg)](https://pypi.org/project/bt_api_ib_web/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/cloudQuant/bt_api_ib_web/actions/workflows/ci.yml/badge.svg)](https://github.com/cloudQuant/bt_api_ib_web)
[![Docs](https://readthedocs.org/projects/bt-api-ib-web/badge/?version=latest)](https://bt-api-ib-web.readthedocs.io/)

---

## English | [中文](#中文)

### Overview

This package provides an **Interactive Brokers Web API gateway adapter** for the [bt_api](https://github.com/cloudQuant/bt_api_py) framework. It connects to IB Web API and exposes a unified interface for trading stocks and futures.

### Features

- **IB WebSocket connection** via `websocket-client`
- **Real-time market data** via WebSocket push notifications
- **Account & position tracking** — balance, positions, orders, trades
- **Order management** — place and cancel orders
- **Stock & futures support** via `asset_type` kwarg (`STK` or `FUT`)
- **Symbol subscription** — batch subscribe by conId or symbol alias

### Requirements

- Python 3.9+
- `bt_api_base >= 0.15`
- `requests >= 2.31`
- `websocket-client >= 1.7`

### Installation

```bash
pip install bt_api_ib_web
```

Or install from source:

```bash
git clone https://github.com/cloudQuant/bt_api_ib_web
cd bt_api_ib_web
pip install -e .
```

### Quick Start

```python
from bt_api_ib_web import IbWebGatewayAdapter

# Initialize the adapter (STK for stocks, FUT for futures)
adapter = IbWebGatewayAdapter(
    base_url="https://localhost:5000",  # IB Web API endpoint
    asset_type="STK",                   # "STK" (stock) or "FUT" (future)
)

# Connect to IB Web API
adapter.connect()

# Subscribe to symbols (by conId or alias)
adapter.subscribe_symbols(["265598", "AAPL"])

# Get account balance
balance = adapter.get_balance()
print(balance)

# Get open positions
positions = adapter.get_positions()
print(positions)

# Place a limit order
order_result = adapter.place_order({
    "symbol": "AAPL",
    "size": 10,
    "price": 150.0,
    "order_type": "limit",
    "side": "buy",
})
print(order_result)

# Cancel an order
cancel_result = adapter.cancel_order({"order_id": "ABC123"})
print(cancel_result)

# Disconnect
adapter.disconnect()
```

### Supported Operations

| Operation | Method | Status |
|-----------|--------|--------|
| Connect | `connect()` | ✅ |
| Disconnect | `disconnect()` | ✅ |
| Subscribe symbols | `subscribe_symbols(symbols)` | ✅ |
| Account balance | `get_balance()` | ✅ |
| Open positions | `get_positions()` | ✅ |
| Place order | `place_order(payload)` | ✅ |
| Cancel order | `cancel_order(payload)` | ✅ |

### Order Payload Format

```python
{
    "symbol": "AAPL",      # Symbol or conId
    "size": 10,            # Order size (volume)
    "price": 150.0,        # Limit price (omit for market orders)
    "order_type": "limit", # "market", "limit", etc.
    "side": "buy",         # "buy" or "sell"
    "client_order_id": "my_ref",   # Optional: client order reference
    "extra_data": {},      # Optional: extra IB parameters
}
```

### Architecture

```
bt_api_ib_web/
├── src/bt_api_ib_web/
│   ├── __init__.py            # Exports IbWebGatewayAdapter
│   ├── plugin.py              # bt_api plugin registration
│   ├── gateway/
│   │   └── adapter.py         # IbWebGatewayAdapter implementation
│   ├── runtime/
│   │   ├── feed.py            # IbWebRequestDataStock / Future
│   │   └── stream.py          # IbWebDataStream / IbWebAccountStream
│   └── containers/
├── tests/
└── docs/
    └── index.md              # Documentation
```

### Online Documentation

| Resource | Link |
|----------|------|
| English Docs | https://bt-api-ib-web.readthedocs.io/ |
| Chinese Docs | https://bt-api-ib-web.readthedocs.io/zh/latest/ |
| GitHub Repository | https://github.com/cloudQuant/bt_api_ib_web |
| Issue Tracker | https://github.com/cloudQuant/bt_api_ib_web/issues |

### License

MIT License - see [LICENSE](LICENSE) for details.

### Support

- Report bugs via [GitHub Issues](https://github.com/cloudQuant/bt_api_ib_web/issues)
- Email: yunjinqi@gmail.com

---

## 中文

### 概述

本包为 [bt_api](https://github.com/cloudQuant/bt_api_py) 框架提供 **Interactive Brokers Web API 网关适配器**。连接 IB Web API，提供股票和期货交易的统一接口。

### 功能特点

- **IB WebSocket 连接** — 通过 `websocket-client` 库
- **实时行情推送** — WebSocket 订阅行情数据
- **账户与持仓跟踪** — 余额、持仓、订单、成交
- **订单管理** — 下单、撤单
- **股票与期货支持** — 通过 `asset_type` 参数（`STK` 或 `FUT`）
- **品种订阅** — 按 conId 或品种别名批量订阅

### 系统要求

- Python 3.9+
- `bt_api_base >= 0.15`
- `requests >= 2.31`
- `websocket-client >= 1.7`

### 安装

```bash
pip install bt_api_ib_web
```

或从源码安装：

```bash
git clone https://github.com/cloudQuant/bt_api_ib_web
cd bt_api_ib_web
pip install -e .
```

### 快速开始

```python
from bt_api_ib_web import IbWebGatewayAdapter

# 初始化适配器（STK 为股票，FUT 为期货）
adapter = IbWebGatewayAdapter(
    base_url="https://localhost:5000",  # IB Web API 端点
    asset_type="STK",                   # "STK"（股票）或 "FUT"（期货）
)

# 连接 IB Web API
adapter.connect()

# 订阅品种（按 conId 或别名）
adapter.subscribe_symbols(["265598", "AAPL"])

# 查询账户余额
balance = adapter.get_balance()
print(balance)

# 查询持仓
positions = adapter.get_positions()
print(positions)

# 下限价单
order_result = adapter.place_order({
    "symbol": "AAPL",
    "size": 10,
    "price": 150.0,
    "order_type": "limit",
    "side": "buy",
})
print(order_result)

# 撤单
cancel_result = adapter.cancel_order({"order_id": "ABC123"})
print(cancel_result)

# 断开连接
adapter.disconnect()
```

### 支持的操作

| 操作 | 方法 | 状态 |
|------|------|------|
| 连接 | `connect()` | ✅ |
| 断开 | `disconnect()` | ✅ |
| 订阅品种 | `subscribe_symbols(symbols)` | ✅ |
| 账户余额 | `get_balance()` | ✅ |
| 持仓查询 | `get_positions()` | ✅ |
| 下单 | `place_order(payload)` | ✅ |
| 撤单 | `cancel_order(payload)` | ✅ |

### 下单参数格式

```python
{
    "symbol": "AAPL",      # 品种名或 conId
    "size": 10,            # 委托数量
    "price": 150.0,        # 限价（市场价单不填）
    "order_type": "limit", # "market", "limit" 等
    "side": "buy",         # "buy" 或 "sell"
    "client_order_id": "my_ref",   # 可选：客户端订单引用
    "extra_data": {},      # 可选：额外 IB 参数
}
```

### 架构

```
bt_api_ib_web/
├── src/bt_api_ib_web/
│   ├── __init__.py            # 导出 IbWebGatewayAdapter
│   ├── plugin.py              # bt_api 插件注册
│   ├── gateway/
│   │   └── adapter.py         # IbWebGatewayAdapter 实现
│   ├── runtime/
│   │   ├── feed.py            # IbWebRequestDataStock / Future
│   │   └── stream.py          # IbWebDataStream / IbWebAccountStream
│   └── containers/
├── tests/
└── docs/
    └── index.md              # 文档
```

### 在线文档

| 资源 | 链接 |
|------|------|
| 英文文档 | https://bt-api-ib-web.readthedocs.io/ |
| 中文文档 | https://bt-api-ib-web.readthedocs.io/zh/latest/ |
| GitHub 仓库 | https://github.com/cloudQuant/bt_api_ib_web |
| 问题反馈 | https://github.com/cloudQuant/bt_api_ib_web/issues |

### 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)。

### 技术支持

- 通过 [GitHub Issues](https://github.com/cloudQuant/bt_api_ib_web/issues) 反馈问题
- 邮箱: yunjinqi@gmail.com
