# Interactive Brokers Web API

Interactive Brokers Web API plugin for bt_api, supporting direct Client Portal feeds and typed projections for stocks and futures.

[![PyPI Version](https://img.shields.io/pypi/v/bt_api_ib_web.svg)](https://pypi.org/project/bt_api_ib_web/)
[![Python Versions](https://img.shields.io/pypi/pyversions/bt_api_ib_web.svg)](https://pypi.org/project/bt_api_ib_web/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/cloudQuant/bt_api_ib_web/actions/workflows/ci.yml/badge.svg)](https://github.com/cloudQuant/bt_api_ib_web)
[![Docs](https://readthedocs.org/projects/bt-api-ib-web/badge/?version=latest)](https://bt-api-ib-web.readthedocs.io/)

---

## English | [中文](#中文)

### Overview

This package provides direct Interactive Brokers Client Portal REST/WebSocket request feeds and typed data containers for the [bt_api](https://github.com/cloudQuant/bt_api_py) framework. `PluginLoader` explicitly calls `register_plugin(registry)` to register the stock and futures feeds; importing the package alone does not mutate a registry.

### Direct projections

- Account balance projection preserves `AvailableFunds` when its value is zero and derives available funds from equity less initial margin when the field is absent.
- Position projection normalizes Client Portal aliases and keeps signed size, absolute volume, and long/short direction.
- Market projection maps Client Portal fields 84, 85, 86, 88, 31, and 87, including the contract ID from an `smd` topic.
- Contract search and details include contract ID, tick size, local symbol, currency, and futures multiplier and expiry when IB returns those fields.

These projections are available to direct feed consumers. They do not create a ServiceHost MarketHub stream or a complete `AccountObservation`. The legacy `IbWebGatewayAdapter` implementation and export have been removed. Managed live writes must use `ServiceExecutionSession` through service-v2 after the provider is integrated with that host.

### Requirements

- Python 3.9+
- `bt_api_base >= 0.15, < 1.0`
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

Live API calls require an accessible, authenticated IB Client Portal Gateway and the required account permissions. Local projection code does not establish a broker session.

### Architecture

```text
bt_api_ib_web/
├── src/bt_api_ib_web/
│   ├── plugin.py              # Explicit feed registration
│   ├── runtime/
│   │   ├── feed.py            # Stock and futures request feeds
│   │   └── stream.py          # Direct market and account streams
│   ├── containers/            # Typed IB Web projections
│   └── configs/               # Package configuration
├── tests/
└── docs/
    └── index.md
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

本包为 [bt_api](https://github.com/cloudQuant/bt_api_py) 框架提供 Interactive Brokers Client Portal REST/WebSocket 直连 feed 和类型化数据容器。`PluginLoader` 会显式调用 `register_plugin(registry)` 注册股票和期货 feed；单独导入包不会修改注册表。

### 直连投影

- 账户余额投影在 `AvailableFunds` 为零时保留零值；字段缺失时，使用权益减初始保证金推导可用资金。
- 持仓投影归一化 Client Portal 字段别名，并保留带符号 size、绝对值 volume 和多空方向。
- 行情投影映射 Client Portal 字段 84、85、86、88、31 和 87，并可从 `smd` topic 解析合约 ID。
- 合约搜索和详情可提供合约 ID、最小跳动、local symbol、币种，以及 IB 返回的期货乘数和到期日。

这些投影供直连 feed 使用者调用，不会创建 ServiceHost MarketHub 行情流，也不是完整的 `AccountObservation`。旧 `IbWebGatewayAdapter` 实现和导出已移除。provider 完成宿主集成后，托管实盘写操作必须通过 service-v2 的 `ServiceExecutionSession`。

### 系统要求

- Python 3.9+
- `bt_api_base >= 0.15, < 1.0`
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

实盘调用需要可访问并已认证的 IB Client Portal Gateway，以及对应账户权限。本地投影代码本身不会建立券商会话。

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
- 邮箱：yunjinqi@gmail.com

## Provider role and integration boundary

`plugin.py` advertises `IB_WEB___STK` and `IB_WEB___FUT` and registers request feeds, typed exchange-data projections, and balance handlers; it does not register `bt_api` stream handlers. This package owns direct IB Client Portal access and projections, not a complete ServiceHost MarketHub stream, `AccountObservation`, or managed write integration. `bt_api_base` supplies the shared plugin protocol and registry; Backtrader owns strategy and backtest logic. Managed writes require provider integration through service-v2 and `ServiceExecutionSession`. See [Trading system architecture](https://github.com/cloudQuant/backtrader/blob/dev/docs/TRADING_SYSTEM_ARCHITECTURE.md).

## 提供方职责与集成边界

`plugin.py` 列出 `IB_WEB___STK` 和 `IB_WEB___FUT`，并注册请求 Feed、类型化交易所数据投影及余额处理器；它没有注册 `bt_api` 流处理器。本包负责直接访问 IB Client Portal 并生成数据投影，不提供完整的 ServiceHost MarketHub 行情流、`AccountObservation` 或托管写入集成。`bt_api_base` 提供共享插件协议和注册表；Backtrader 负责策略与回测逻辑。托管写操作还需通过 service-v2 和 `ServiceExecutionSession` 完成 provider 集成。架构说明：[Trading system architecture](https://github.com/cloudQuant/backtrader/blob/dev/docs/TRADING_SYSTEM_ARCHITECTURE.md)。
