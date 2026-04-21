# Interactive Brokers Web API Documentation

## English

Welcome to the Interactive Brokers Web API documentation for bt_api.

### Quick Start

```bash
pip install bt_api_ib_web
```

```python
from bt_api_ib_web import IBWebApi
feed = IBWebApi(api_key="your_key", secret="your_secret")
ticker = feed.get_ticker("AAPL")
```

## 中文

欢迎使用 bt_api 的 盈透证券Web API 文档。

### 快速开始

```bash
pip install bt_api_ib_web
```

```python
from bt_api_ib_web import IBWebApi
feed = IBWebApi(api_key="your_key", secret="your_secret")
ticker = feed.get_ticker("AAPL")
```

## API Reference

See source code in `src/bt_api_ib_web/` for detailed API documentation.
