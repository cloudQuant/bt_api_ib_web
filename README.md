# Interactive Brokers Web API

Interactive Brokers Web API plugin for bt_api, supporting stock trading.

[![PyPI Version](https://img.shields.io/pypi/v/bt_api_ib_web.svg)](https://pypi.org/project/bt_api_ib_web/)
[![Python Versions](https://img.shields.io/pypi/pyversions/bt_api_ib_web.svg)](https://pypi.org/project/bt_api_ib_web/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/cloudQuant/bt_api_ib_web/actions/workflows/ci.yml/badge.svg)](https://github.com/cloudQuant/bt_api_ib_web/actions)
[![Docs](https://readthedocs.org/projects/bt-api-ib-web/badge/?version=latest)](https://bt-api-ib-web.readthedocs.io/)

---

## English | [中文](#中文)

### Overview

This package provides **Interactive Brokers Web API plugin for bt_api** for the [bt_api](https://github.com/cloudQuant/bt_api_py) framework. It offers a unified interface for interacting with **Interactive Brokers Web API** exchange.

### Features

- Stock trading via IB Web API
- Real-time market data
- Portfolio and position tracking
- Order management
- Multi-asset support

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
from bt_api_ib_web import IBWebApi

# Initialize
feed = IBWebApi(api_key="your_key", secret="your_secret")

# Get ticker data
ticker = feed.get_ticker("AAPL")
print(ticker)
```

### Supported Operations

| Operation | Status |
|-----------|--------|
| Ticker | ✅ |
| OrderBook | ✅ |
| Trades | ✅ |
| Bars/Klines | ✅ |
| Orders | ✅ |
| Balances | ✅ |
| Positions | ✅ |

### Online Documentation

| Resource | Link |
|----------|------|
| English Docs | https://bt-api-ib-web.readthedocs.io/ |
| Chinese Docs | https://bt-api-ib-web.readthedocs.io/zh/latest/ |
| GitHub Repository | https://github.com/cloudQuant/bt_api_ib_web |
| Issue Tracker | https://github.com/cloudQuant/bt_api_ib_web/issues |

### Requirements

- Python 3.9+
- bt_api_base >= 0.15

### Architecture

```
bt_api_ib_web/
├── src/bt_api_ib_web/     # Source code
│   ├── containers/     # Data containers
│   ├── feeds/          # API feeds
│   ├── gateway/       # Gateway adapter
│   └── plugin.py      # Plugin registration
├── tests/             # Unit tests
└── docs/             # Documentation
```

### License

MIT License - see [LICENSE](LICENSE) for details.

### Support

- Report bugs via [GitHub Issues](https://github.com/cloudQuant/bt_api_ib_web/issues)
- Email: yunjinqi@gmail.com

---

## 中文

### 概述

本包为 [bt_api](https://github.com/cloudQuant/bt_api_py) 框架提供 **Interactive Brokers Web API plugin for bt_api**。它提供了与 **盈透证券Web API** 交易所交互的统一接口。

### 功能特点

- 通过IB Web API进行股票交易
- 实时市场数据
- 投资组合和持仓跟踪
- 订单管理
- 多资产支持

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
from bt_api_ib_web import IBWebApi

# 初始化
feed = IBWebApi(api_key="your_key", secret="your_secret")

# 获取行情数据
ticker = feed.get_ticker("AAPL")
print(ticker)
```

### 支持的操作

| 操作 | 状态 |
|------|------|
| Ticker | ✅ |
| OrderBook | ✅ |
| Trades | ✅ |
| Bars/Klines | ✅ |
| Orders | ✅ |
| Balances | ✅ |
| Positions | ✅ |

### 在线文档

| 资源 | 链接 |
|------|------|
| 英文文档 | https://bt-api-ib-web.readthedocs.io/ |
| 中文文档 | https://bt-api-ib-web.readthedocs.io/zh/latest/ |
| GitHub 仓库 | https://github.com/cloudQuant/bt_api_ib_web |
| 问题反馈 | https://github.com/cloudQuant/bt_api_ib_web/issues |

### 系统要求

- Python 3.9+
- bt_api_base >= 0.15

### 架构

```
bt_api_ib_web/
├── src/bt_api_ib_web/     # 源代码
│   ├── containers/     # 数据容器
│   ├── feeds/          # API 源
│   ├── gateway/        # 网关适配器
│   └── plugin.py       # 插件注册
├── tests/             # 单元测试
└── docs/             # 文档
```

### 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)。

### 技术支持

- 通过 [GitHub Issues](https://github.com/cloudQuant/bt_api_ib_web/issues) 反馈问题
- 邮箱: yunjinqi@gmail.com
