# Interactive Brokers Web API Documentation

## English

bt_api_ib_web provides direct Client Portal feeds and typed containers for IB stocks and futures. PluginLoader explicitly registers the STK and FUT feeds by calling register_plugin(registry).

Package-level projections include account balance fields, Client Portal position aliases, market snapshot fields 84/85/86/88/31/87 with topic conid, and direct contract search/details including futures multiplier and expiry. These projections are usable by direct feed consumers.

The legacy `IbWebGatewayAdapter` implementation and export have been removed. This package does not create ServiceHost MarketHub or complete AccountObservation projections, or claim a managed service integration. Live managed writes must go through ServiceExecutionSession and service-v2 after host integration.

See the README for requirements and supported projection details.

## 中文

bt_api_ib_web 提供 IB 股票和期货的 Client Portal 直连 feed 与类型化容器。PluginLoader 通过显式调用 register_plugin(registry) 注册 STK 和 FUT feed。

包级投影包含账户余额字段、Client Portal 持仓别名、含 topic conid 的行情字段 84/85/86/88/31/87，以及包含期货乘数和到期日的直连合约搜索/详情。直连 feed 使用者可以调用这些投影。

旧 `IbWebGatewayAdapter` 实现和导出已移除。当前包不构造 ServiceHost MarketHub 或完整 AccountObservation 投影，也不代表托管服务集成已经完成。宿主集成后，托管实盘写操作应经由 ServiceExecutionSession 和 service-v2。

要求和投影边界见 README。
