from dataclasses import dataclass
from datetime import datetime
from typing import Literal


Direction = Literal["long", "short", "flat"]


@dataclass(frozen=True)
class Bar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    strategy_id: str
    symbol: str
    direction: Direction
    confidence: float
    timestamp: datetime


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: Literal["buy", "sell"]
    quantity: int
    current_quantity: int
    target_quantity: int
    target_weight: float
    reference_price: float


@dataclass(frozen=True)
class BlockedOrderIntent:
    intent: OrderIntent
    reason: str
