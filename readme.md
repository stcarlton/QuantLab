# QuantLab

QuantLab is a modular algorithmic trading framework in Python, built incrementally toward a production-grade meta-strategy platform.

## Purpose
- Build a meta-strategy system from scratch.
- Maintain independent strategy modules.
- Allocate capital across strategies via a meta layer.
- Enforce global risk before execution.
- Validate with paper trading before any live deployment.

## Core Principles
- Separation of concerns by layer.
- Deterministic, testable components.
- Strategies generate signals only.
- Allocation and risk are centralized.
- Execution is isolated behind broker adapters.

## High-Level Architecture
```text
Data -> Strategies -> Meta Allocation -> Risk -> Execution -> Broker -> Database
```

Each layer is independently replaceable through clear interfaces.

## Project Structure
```text
src/quantlab/
  config.py
  engine.py
  main.py
  types.py
  runtime/
    engine_loop.py
  data/
    loader.py
    storage.py
  strategies/
    base_strategy.py
    momentum.py
  regime/
    regime_model.py
  meta/
    allocator.py
    performance_tracker.py
  risk/
    risk_manager.py
  execution/
    broker_interface.py
    paper_executor.py
    alpaca_broker.py
  db/
    models.py
    repository.py
  scripts/
    check_alpaca_connection.py
    place_test_order.py
    check_order_status.py
    poll_order_status.py
    reconcile_orders.py
    inspect_state.py
    cancel_open_orders.py

docs/
  requirements.md
  architecture.md
  alpaca_setup.md
```

## Layer Responsibilities
1. `data`: Load and normalize market data.
2. `strategies`: Emit standardized `Signal` objects.
3. `meta`: Convert strategy signals to target weights.
4. `risk`: Enforce portfolio and position constraints.
5. `execution`: Translate approved intents into broker actions.
6. `db`: Persist orders, fills, positions, and metrics.
7. `engine`: Orchestrate the pipeline only.

## Delivery Strategy
1. Contracts and interfaces.
2. Single-strategy historical loop.
3. Allocation plus risk integration.
4. Paper execution and reconciliation.
5. Persistence and metrics.
6. Multi-strategy expansion.
7. Regime-aware scaling.

## Current Status
- Base scaffold is in place.
- Alpaca paper connectivity is working.
- Paper order placement and order-status scripts are available.

## Local Setup
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run tests:
```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

## Debug and Run
Use a direct Python entrypoint:
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.main
```

For debugging/test runs, set overrides in code in `src/quantlab/main.py`:
```python
DEBUG_SETTINGS_OVERRIDES = {
    # "run_loop": True,
    # "loop_interval_seconds": 30,
    # "loop_timeout_seconds": 0,
    # "submit_orders": False,
}
```

## Alpaca Paper Workflow
Use the detailed guide in `docs/alpaca_setup.md`.

Quick start:
```powershell
$env:APCA_API_KEY_ID="your_key_id"
$env:APCA_API_SECRET_KEY="your_secret_key"
$env:APCA_API_BASE_URL="https://paper-api.alpaca.markets"
$env:PYTHONPATH="src"

.\.venv\Scripts\python.exe -m quantlab.scripts.check_alpaca_connection
.\.venv\Scripts\python.exe -m quantlab.scripts.place_test_order --symbol AAPL --qty 1 --side buy --yes
.\.venv\Scripts\python.exe -m quantlab.scripts.reconcile_orders
.\.venv\Scripts\python.exe -m quantlab.scripts.inspect_state --limit 5
```

## Engine Run (Full Path)
Default safe run (no order submission):
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.main
```

Runtime knobs:
- `QL_SYMBOL` (default `AAPL`)
- `QL_UNIVERSE_MODE` (`static` or `alpaca_assets`, default `static`)
- `QL_SYMBOLS` (comma-separated static universe, e.g. `AAPL,MSFT,SPY`)
- `QL_UNIVERSE_LIMIT` (default `50`, used by `alpaca_assets`)
- `QL_DATA_SOURCE` (`synthetic` or `csv`, default `synthetic`)
- `QL_DATA_CSV_PATH` (required if `QL_DATA_SOURCE=csv`)
- `QL_ALPACA_DATA_MODE` (`latest`, `historical`, or `stream`, default `latest`, used when `QL_DATA_SOURCE=alpaca`)
- `QL_ALPACA_DATA_FEED` (default `iex`, free plan friendly)
- `QL_ALPACA_STREAM_URL` (default `wss://stream.data.alpaca.markets`, stream mode)
- `QL_ALPACA_STREAM_WAIT_SECONDS` (default `10`, stream mode startup wait)
- `QL_ALPACA_DATA_TIMEFRAME` (default `1Min`, for historical mode)
- `QL_ALPACA_HISTORY_LIMIT` (default `100`, for historical mode)
- `QL_ALPACA_HISTORY_START` (optional ISO timestamp, historical mode)
- `QL_ALPACA_HISTORY_END` (optional ISO timestamp, historical mode)
- `QL_EXECUTION_PROVIDER` (`paper_stub` or `alpaca_paper`, default `paper_stub`)
- `QL_SUBMIT_ORDERS` (`true` or `false`, default `false`)
- `QL_RUN_LOOP` (`true` or `false`, default `false`)
- `QL_LOOP_INTERVAL_SECONDS` (default `60`)
- `QL_LOOP_TIMEOUT_SECONDS` (default `0`, meaning no timeout)
- `QL_DB_PATH` (default `.quantlab/quantlab.db`)
- `QL_MAX_ORDER_NOTIONAL` (default `1000000`)
- `QL_DAILY_LOSS_LIMIT_PCT` (default `1.0`, fraction of starting cash)
- `QL_KILL_SWITCH` (`true` or `false`, default `false`)
- `QL_ALLOW_SHORT` (`true` or `false`, default `false`)
- `QL_STATE_PATH` (default `.quantlab/portfolio_state.json`)
- `QL_REBALANCE_LOG_PATH` (default `.quantlab/rebalance_log.jsonl`)
- `QL_ORDER_EVENT_LOG_PATH` (default `.quantlab/order_events.jsonl`)

Sizing behavior:
- Engine converts target weights into share quantities using `starting_cash` and latest bar close.
- Orders are delta-based against persisted current positions from `QL_STATE_PATH`.
- Universe selection runs before data loading (`static` symbols list or `alpaca_assets`).
- In `alpaca_paper` mode, current positions are reconciled from broker `list_positions()` before sizing.
- In `alpaca_paper` mode, sizing equity is reconciled from broker `get_account()` (fallback: `starting_cash`).
- If an open broker order already exists for a symbol, submission is skipped for that symbol in that run.
- In `alpaca_paper` mode, pending submitted order ids are reconciled each run via `get_order()` and terminal events are logged.
- State and event logs are persisted in SQLite (`QL_DB_PATH`) with query helpers in `Repository`.
- Ingested market bars are persisted to SQLite (`market_bars`) before strategy evaluation.
- Risk v1 guards: max order notional, daily loss limit, and kill switch block orders before submission.
- If `QL_ALLOW_SHORT=false`, sizing clamps negative targets to zero (no net short positions).

Example using Alpaca paper execution:
```powershell
$env:PYTHONPATH="src"
$env:QL_SYMBOL="AAPL"
$env:QL_EXECUTION_PROVIDER="alpaca_paper"
$env:QL_SUBMIT_ORDERS="false"
.\.venv\Scripts\python.exe -m quantlab.main
```

Example using Alpaca data ingestion (latest bars, loop):
```powershell
$env:PYTHONPATH="src"
$env:QL_DATA_SOURCE="alpaca"
$env:QL_ALPACA_DATA_MODE="latest"
$env:QL_ALPACA_DATA_FEED="iex"
$env:QL_RUN_LOOP="true"
$env:QL_LOOP_INTERVAL_SECONDS="30"
$env:QL_LOOP_TIMEOUT_SECONDS="300"
.\.venv\Scripts\python.exe -m quantlab.main
```

Example using Alpaca websocket stream ingestion:
```powershell
$env:PYTHONPATH="src"
$env:QL_DATA_SOURCE="alpaca"
$env:QL_ALPACA_DATA_MODE="stream"
$env:QL_ALPACA_DATA_FEED="iex"
$env:QL_ALPACA_STREAM_URL="wss://stream.data.alpaca.markets"
$env:QL_ALPACA_STREAM_WAIT_SECONDS="10"
$env:QL_RUN_LOOP="true"
$env:QL_LOOP_INTERVAL_SECONDS="30"
.\.venv\Scripts\python.exe -m quantlab.main
```

Example loop mode:
```powershell
$env:PYTHONPATH="src"
$env:QL_RUN_LOOP="true"
$env:QL_LOOP_INTERVAL_SECONDS="30"
$env:QL_LOOP_TIMEOUT_SECONDS="300"
.\.venv\Scripts\python.exe -m quantlab.main
```

## Notes
- Start in paper mode only.
- Keep broker credentials in environment variables.
- Build incrementally without crossing layer boundaries.
