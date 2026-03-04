import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from quantlab.db.models import MarketBarRecord, OrderEventRecord, PortfolioState, RebalanceRecord
from quantlab.types import Bar


class Repository:
    def __init__(
        self,
        db_path: str = ".quantlab/quantlab.db",
        state_path: str | None = None,
        rebalance_log_path: str | None = None,
        order_event_log_path: str | None = None,
    ) -> None:
        # Legacy path args are accepted for compatibility; SQLite is the active backend.
        _ = state_path, rebalance_log_path, order_event_log_path
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    current_positions_json TEXT NOT NULL,
                    last_target_weights_json TEXT NOT NULL,
                    last_rebalance_at TEXT,
                    pending_order_ids_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rebalance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    execution_provider TEXT NOT NULL,
                    equity_used REAL NOT NULL,
                    signal_count INTEGER NOT NULL,
                    target_weights_json TEXT NOT NULL,
                    planned_order_count INTEGER NOT NULL,
                    submitted_order_count INTEGER NOT NULL,
                    skipped_due_to_open_orders_json TEXT NOT NULL,
                    reconciled_terminal_order_count INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS order_event_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    symbol TEXT,
                    filled_qty TEXT,
                    filled_avg_price TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_bars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    source TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,
                    UNIQUE(symbol, timestamp, source)
                )
                """
            )
            conn.commit()

    def load_portfolio_state(self) -> PortfolioState:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM portfolio_state WHERE id = 1").fetchone()
        if row is None:
            return PortfolioState()
        return PortfolioState(
            current_positions={k: int(v) for k, v in json.loads(row["current_positions_json"]).items()},
            last_target_weights={k: float(v) for k, v in json.loads(row["last_target_weights_json"]).items()},
            last_rebalance_at=row["last_rebalance_at"],
            pending_order_ids=[str(item) for item in json.loads(row["pending_order_ids_json"])],
        )

    def save_portfolio_state(self, state: PortfolioState) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO portfolio_state (
                    id, current_positions_json, last_target_weights_json, last_rebalance_at, pending_order_ids_json
                )
                VALUES (1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    current_positions_json=excluded.current_positions_json,
                    last_target_weights_json=excluded.last_target_weights_json,
                    last_rebalance_at=excluded.last_rebalance_at,
                    pending_order_ids_json=excluded.pending_order_ids_json
                """,
                (
                    json.dumps(state.current_positions),
                    json.dumps(state.last_target_weights),
                    state.last_rebalance_at,
                    json.dumps(state.pending_order_ids),
                ),
            )
            conn.commit()

    def append_rebalance_record(self, record: RebalanceRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rebalance_records (
                    timestamp, symbol, execution_provider, equity_used, signal_count, target_weights_json,
                    planned_order_count, submitted_order_count, skipped_due_to_open_orders_json,
                    reconciled_terminal_order_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.timestamp,
                    record.symbol,
                    record.execution_provider,
                    record.equity_used,
                    record.signal_count,
                    json.dumps(record.target_weights),
                    record.planned_order_count,
                    record.submitted_order_count,
                    json.dumps(record.skipped_due_to_open_orders),
                    record.reconciled_terminal_order_count,
                ),
            )
            conn.commit()

    def append_order_event(self, record: OrderEventRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO order_event_records (
                    timestamp, order_id, status, symbol, filled_qty, filled_avg_price
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.timestamp,
                    record.order_id,
                    record.status,
                    record.symbol,
                    record.filled_qty,
                    record.filled_avg_price,
                ),
            )
            conn.commit()

    def query_recent_rebalances(self, limit: int = 20) -> list[RebalanceRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM rebalance_records
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        records: list[RebalanceRecord] = []
        for row in rows:
            records.append(
                RebalanceRecord(
                    timestamp=row["timestamp"],
                    symbol=row["symbol"],
                    execution_provider=row["execution_provider"],
                    equity_used=float(row["equity_used"]),
                    signal_count=int(row["signal_count"]),
                    target_weights={k: float(v) for k, v in json.loads(row["target_weights_json"]).items()},
                    planned_order_count=int(row["planned_order_count"]),
                    submitted_order_count=int(row["submitted_order_count"]),
                    skipped_due_to_open_orders=[str(x) for x in json.loads(row["skipped_due_to_open_orders_json"])],
                    reconciled_terminal_order_count=int(row["reconciled_terminal_order_count"]),
                )
            )
        return records

    def query_recent_order_events(self, limit: int = 20) -> list[OrderEventRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM order_event_records
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        events: list[OrderEventRecord] = []
        for row in rows:
            events.append(
                OrderEventRecord(
                    timestamp=row["timestamp"],
                    order_id=row["order_id"],
                    status=row["status"],
                    symbol=row["symbol"],
                    filled_qty=row["filled_qty"],
                    filled_avg_price=row["filled_avg_price"],
                )
            )
        return events

    def save_market_bars(self, bars: list[Bar], source: str) -> int:
        if not bars:
            return 0
        ingested_at = datetime.now(tz=timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.executemany(
                """
                INSERT INTO market_bars (
                    timestamp, symbol, open, high, low, close, volume, source, ingested_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, timestamp, source) DO UPDATE SET
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume,
                    ingested_at=excluded.ingested_at
                """,
                [
                    (
                        bar.timestamp.isoformat(),
                        bar.symbol,
                        float(bar.open),
                        float(bar.high),
                        float(bar.low),
                        float(bar.close),
                        float(bar.volume),
                        source,
                        ingested_at,
                    )
                    for bar in bars
                ],
            )
            conn.commit()
            return cursor.rowcount if cursor.rowcount is not None else len(bars)

    def query_recent_market_bars(self, limit: int = 20, symbol: str | None = None) -> list[MarketBarRecord]:
        with self._connect() as conn:
            if symbol:
                rows = conn.execute(
                    """
                    SELECT * FROM market_bars
                    WHERE symbol = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (symbol, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM market_bars
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        bars: list[MarketBarRecord] = []
        for row in rows:
            bars.append(
                MarketBarRecord(
                    timestamp=row["timestamp"],
                    symbol=row["symbol"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                    source=row["source"],
                    ingested_at=row["ingested_at"],
                )
            )
        return bars

    def save_trade(self) -> None:
        return None
