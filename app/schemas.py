from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Candle:
    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Position:
    symbol: str
    amount: float = 0.0
    avg_price: float = 0.0
    last_price: float = 0.0


@dataclass
class Decision:
    action: str
    symbol: str
    reason: str
    price: float
    amount: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)
