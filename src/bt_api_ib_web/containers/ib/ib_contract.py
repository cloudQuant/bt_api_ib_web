from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class IbContract:
    symbol: Any = ""
    sec_type: Any = "STK"
    exchange: Any = "SMART"
    currency: Any = "USD"
    con_id: Any = 0
    last_trade_date: Any = ""
    strike: Any = 0.0
    right: Any = ""
    multiplier: Any = ""
    primary_exchange: Any = ""
    local_symbol: Any = ""
    trading_class: Any = ""

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if value}

    def __str__(self) -> str:
        parts = [self.symbol, self.sec_type, self.exchange, self.currency]
        if self.last_trade_date:
            parts.append(self.last_trade_date)
        if self.strike:
            parts.append(str(self.strike))
        if self.right:
            parts.append(self.right)
        return " ".join(str(part) for part in parts if part is not None)

    def __repr__(self) -> str:
        return f"IbContract({self})"

    @classmethod
    def stock(
        cls, symbol: Any, exchange: Any = "SMART", currency: Any = "USD"
    ) -> IbContract:
        return cls(symbol=symbol, sec_type="STK", exchange=exchange, currency=currency)

    @classmethod
    def future(
        cls,
        symbol: Any,
        exchange: Any = "GLOBEX",
        currency: Any = "USD",
        last_trade_date: Any = "",
    ) -> IbContract:
        return cls(
            symbol=symbol,
            sec_type="FUT",
            exchange=exchange,
            currency=currency,
            last_trade_date=last_trade_date,
        )

    @classmethod
    def option(
        cls,
        symbol: Any,
        last_trade_date: Any,
        strike: Any,
        right: Any,
        exchange: Any = "SMART",
        currency: Any = "USD",
    ) -> IbContract:
        return cls(
            symbol=symbol,
            sec_type="OPT",
            exchange=exchange,
            currency=currency,
            last_trade_date=last_trade_date,
            strike=strike,
            right=right,
        )

    @classmethod
    def forex(
        cls, symbol: Any, exchange: Any = "IDEALPRO", currency: Any = "USD"
    ) -> IbContract:
        return cls(symbol=symbol, sec_type="CASH", exchange=exchange, currency=currency)
