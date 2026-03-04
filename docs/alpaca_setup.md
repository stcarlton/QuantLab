# Alpaca Paper Setup

## 1. Set environment variables (PowerShell)
```powershell
$env:APCA_API_KEY_ID="your_key_id"
$env:APCA_API_SECRET_KEY="your_secret_key"
$env:APCA_API_BASE_URL="https://paper-api.alpaca.markets"
```

Optional: store in `.env` (recommended). `.env` is gitignored.

## 2. Verify connection
Run from project root:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.scripts.check_alpaca_connection
```

## 3. Submit a paper order (from code)
```python
from quantlab.config import Settings
from quantlab.execution.alpaca_broker import AlpacaBroker

settings = Settings()
settings.require_alpaca_credentials()

broker = AlpacaBroker(
    key_id=settings.alpaca_key_id or "",
    secret_key=settings.alpaca_secret_key or "",
    base_url=settings.alpaca_base_url,
)

order = broker.submit_order(symbol="AAPL", quantity=1, side="buy")
print(order)
```

## 4. Submit a paper order (CLI, safer)
Dry run (no order submitted):
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.scripts.place_test_order --symbol AAPL --qty 1 --side buy
```

Submit live paper order:
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.scripts.place_test_order --symbol AAPL --qty 1 --side buy --yes
```

## 5. Check order status by ID
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.scripts.check_order_status --order-id your_order_id_here
```

## 6. Poll order status until terminal
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.scripts.poll_order_status --order-id your_order_id_here --interval-seconds 5 --timeout-seconds 600
```

## 7. Reconcile pending orders from local state
Single pass:
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.scripts.reconcile_orders
```

Loop mode:
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.scripts.reconcile_orders --loop --interval-seconds 30 --timeout-seconds 600
```

## 8. Inspect local state (SQLite)
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.scripts.inspect_state --limit 5
```

## 9. Safely cancel open paper orders
Dry run:
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.scripts.cancel_open_orders --symbol AAPL --max-orders 5
```

Execute cancellation:
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.scripts.cancel_open_orders --symbol AAPL --max-orders 5 --yes
```

## 10. Stream bars over websocket (engine ingestion)
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

## 11. Run the engine directly
Single run:
```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m quantlab.main
```

Loop mode:
```powershell
$env:PYTHONPATH="src"
$env:QL_RUN_LOOP="true"
$env:QL_LOOP_INTERVAL_SECONDS="30"
.\.venv\Scripts\python.exe -m quantlab.main
```

Optional: for debug/test convenience, set `DEBUG_SETTINGS_OVERRIDES` in `src/quantlab/main.py`.
