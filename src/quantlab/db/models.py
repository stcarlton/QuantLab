from dataclasses import dataclass, field


@dataclass
class PortfolioState:
    current_positions: dict[str, int] = field(default_factory=dict)
    last_target_weights: dict[str, float] = field(default_factory=dict)
    last_rebalance_at: str | None = None
    pending_order_ids: list[str] = field(default_factory=list)


@dataclass
class RebalanceRecord:
    timestamp: str
    symbol: str
    execution_provider: str
    equity_used: float
    signal_count: int
    target_weights: dict[str, float]
    planned_order_count: int
    submitted_order_count: int
    skipped_due_to_open_orders: list[str] = field(default_factory=list)
    reconciled_terminal_order_count: int = 0


@dataclass
class OrderEventRecord:
    timestamp: str
    order_id: str
    status: str
    symbol: str | None = None
    filled_qty: str | None = None
    filled_avg_price: str | None = None


@dataclass
class MarketBarRecord:
    timestamp: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
    ingested_at: str


class TradeRecord:
    pass
