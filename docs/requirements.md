# Trading Platform Requirements

## 1. Vision
Build a modular Python trading platform from scratch that supports research, paper trading, and eventual live deployment with strict risk controls.

## 2. Scope (Phase 1)
- Ingest historical OHLCV market data.
- Define a standard strategy interface and signal format.
- Run at least one baseline strategy end-to-end.
- Add a portfolio allocator that maps signals to target weights.
- Add global risk checks before execution.
- Simulate execution in paper mode.
- Persist trades, positions, and performance metrics.

## 3. Out of Scope (Phase 1)
- Live brokerage execution.
- Options/futures support.
- Multi-asset portfolio optimization.
- Distributed architecture.

## 4. Functional Requirements
- Data module loads and validates historical bars.
- Strategy module emits standardized `Signal` objects.
- Allocation module converts signals into target portfolio weights.
- Risk module enforces max position size, max gross exposure, and stop-loss rules.
- Execution module simulates fills with configurable slippage/fees.
- Logging module records orders, fills, PnL, drawdown, and key metrics.

## 5. Non-Functional Requirements
- Deterministic backtests given identical inputs.
- Clear module boundaries and testable interfaces.
- Config-driven behavior (YAML/TOML/env).
- Basic test coverage for core interfaces and risk rules.

## 6. Initial Tech Stack
- Python 3.12+
- pandas
- numpy
- pydantic
- pyyaml
- sqlalchemy
- pytest

## 7. Milestones
1. Project scaffold + core interfaces.
2. Single-strategy backtest loop.
3. Portfolio + risk integration.
4. Paper execution + persistence.
5. Metrics/reporting baseline.
