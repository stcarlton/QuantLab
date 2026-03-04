import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


def _load_dotenv(dotenv_path: str = ".env") -> None:
    path = Path(dotenv_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if not key:
            continue
        if os.getenv(key) is None:
            os.environ[key] = value


_load_dotenv()


def _execution_provider_from_env() -> Literal["paper_stub", "alpaca_paper"]:
    value = os.getenv("QL_EXECUTION_PROVIDER", "paper_stub")
    if value not in {"paper_stub", "alpaca_paper"}:
        raise ValueError("QL_EXECUTION_PROVIDER must be 'paper_stub' or 'alpaca_paper'.")
    return value


def _universe_mode_from_env() -> Literal["static", "alpaca_assets"]:
    value = os.getenv("QL_UNIVERSE_MODE", "static")
    if value not in {"static", "alpaca_assets"}:
        raise ValueError("QL_UNIVERSE_MODE must be 'static' or 'alpaca_assets'.")
    return value


def _data_source_from_env() -> Literal["synthetic", "csv", "alpaca"]:
    value = os.getenv("QL_DATA_SOURCE", "synthetic")
    if value not in {"synthetic", "csv", "alpaca"}:
        raise ValueError("QL_DATA_SOURCE must be 'synthetic', 'csv', or 'alpaca'.")
    return value


def _alpaca_data_mode_from_env() -> Literal["latest", "historical", "stream"]:
    value = os.getenv("QL_ALPACA_DATA_MODE", "latest")
    if value not in {"latest", "historical", "stream"}:
        raise ValueError("QL_ALPACA_DATA_MODE must be 'latest', 'historical', or 'stream'.")
    return value


@dataclass(frozen=True)
class Settings:
    environment: str = "dev"
    starting_cash: float = 100_000.0
    max_position_weight: float = 0.10
    max_gross_exposure: float = 1.0
    max_order_notional: float = field(default_factory=lambda: float(os.getenv("QL_MAX_ORDER_NOTIONAL", "1000000")))
    daily_loss_limit_pct: float = field(default_factory=lambda: float(os.getenv("QL_DAILY_LOSS_LIMIT_PCT", "1.0")))
    kill_switch: bool = field(default_factory=lambda: os.getenv("QL_KILL_SWITCH", "false").lower() == "true")
    allow_short: bool = field(default_factory=lambda: os.getenv("QL_ALLOW_SHORT", "false").lower() == "true")
    symbol: str = field(default_factory=lambda: os.getenv("QL_SYMBOL", "AAPL"))
    symbols_csv: str | None = field(default_factory=lambda: os.getenv("QL_SYMBOLS"))
    universe_mode: Literal["static", "alpaca_assets"] = field(default_factory=_universe_mode_from_env)
    universe_limit: int = field(default_factory=lambda: int(os.getenv("QL_UNIVERSE_LIMIT", "50")))
    data_source: Literal["synthetic", "csv", "alpaca"] = field(default_factory=_data_source_from_env)
    data_csv_path: str | None = field(default_factory=lambda: os.getenv("QL_DATA_CSV_PATH"))
    alpaca_data_mode: Literal["latest", "historical", "stream"] = field(default_factory=_alpaca_data_mode_from_env)
    alpaca_data_base_url: str = field(default_factory=lambda: os.getenv("APCA_DATA_BASE_URL", "https://data.alpaca.markets"))
    alpaca_data_feed: str = field(default_factory=lambda: os.getenv("QL_ALPACA_DATA_FEED", "iex"))
    alpaca_data_timeframe: str = field(default_factory=lambda: os.getenv("QL_ALPACA_DATA_TIMEFRAME", "1Min"))
    alpaca_data_history_limit: int = field(default_factory=lambda: int(os.getenv("QL_ALPACA_HISTORY_LIMIT", "100")))
    alpaca_data_history_start: str | None = field(default_factory=lambda: os.getenv("QL_ALPACA_HISTORY_START"))
    alpaca_data_history_end: str | None = field(default_factory=lambda: os.getenv("QL_ALPACA_HISTORY_END"))
    alpaca_stream_url: str = field(
        default_factory=lambda: os.getenv("QL_ALPACA_STREAM_URL", "wss://stream.data.alpaca.markets")
    )
    alpaca_stream_wait_seconds: int = field(default_factory=lambda: int(os.getenv("QL_ALPACA_STREAM_WAIT_SECONDS", "10")))
    execution_provider: Literal["paper_stub", "alpaca_paper"] = field(default_factory=_execution_provider_from_env)
    submit_orders: bool = field(default_factory=lambda: os.getenv("QL_SUBMIT_ORDERS", "false").lower() == "true")
    run_loop: bool = field(default_factory=lambda: os.getenv("QL_RUN_LOOP", "false").lower() == "true")
    loop_interval_seconds: int = field(default_factory=lambda: int(os.getenv("QL_LOOP_INTERVAL_SECONDS", "60")))
    loop_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("QL_LOOP_TIMEOUT_SECONDS", "0")))
    db_path: str = field(default_factory=lambda: os.getenv("QL_DB_PATH", ".quantlab/quantlab.db"))
    state_path: str = field(default_factory=lambda: os.getenv("QL_STATE_PATH", ".quantlab/portfolio_state.json"))
    rebalance_log_path: str = field(default_factory=lambda: os.getenv("QL_REBALANCE_LOG_PATH", ".quantlab/rebalance_log.jsonl"))
    order_event_log_path: str = field(
        default_factory=lambda: os.getenv("QL_ORDER_EVENT_LOG_PATH", ".quantlab/order_events.jsonl")
    )
    alpaca_key_id: str | None = field(default_factory=lambda: os.getenv("APCA_API_KEY_ID"))
    alpaca_secret_key: str | None = field(default_factory=lambda: os.getenv("APCA_API_SECRET_KEY"))
    alpaca_base_url: str = field(
        default_factory=lambda: os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    )

    def require_alpaca_credentials(self) -> None:
        if not self.alpaca_key_id or not self.alpaca_secret_key:
            raise ValueError(
                "Missing Alpaca credentials. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY environment variables."
            )
