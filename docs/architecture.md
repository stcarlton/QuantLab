# QuantLab Architecture Contract

## Goal
Build toward a production-ready meta-strategy trading platform incrementally, with stable boundaries so each phase adds capability without rework.

## Stable Layer Boundaries
1. `data`: Loads normalized market bars/events; no strategy logic.
2. `strategies`: Converts market inputs to standardized `Signal`; no capital allocation or order placement.
3. `meta`: Aggregates strategy signals into target portfolio weights.
4. `risk`: Enforces portfolio constraints and modifies/rejects unsafe targets.
5. `execution`: Converts approved targets/orders into broker API actions.
6. `db`: Persists orders, fills, positions, and metrics.
7. `engine`: Orchestrates flow across layers; no domain logic inside engine methods.

## Core Invariants
1. Strategy code must never call broker APIs directly.
2. Risk checks must be applied after allocation and before execution.
3. Execution adapters must be swappable (`paper_stub`, `alpaca_paper`) without strategy changes.
4. Shared data models (`Bar`, `Signal`) remain backward-compatible whenever possible.
5. Environment-specific values live in config/env, not hardcoded in modules.

## Runtime Modes
1. `research`: historical data, no broker calls.
2. `paper`: broker calls allowed only against paper endpoints.
3. `live`: reserved for future; requires extra guardrails and explicit opt-in.

## Incremental Delivery Sequence
1. Foundation: domain models + interface contracts + config loading.
2. Single-symbol loop: one strategy emits signals from historical bars.
3. Portfolio path: signal aggregation -> allocator -> risk validation.
4. Execution path: broker adapter + order status reconciliation.
5. Persistence: durable logging for orders/fills/positions/metrics.
6. Portfolio expansion: multi-symbol and multi-strategy scheduling.
7. Regime-aware allocation and risk scaling.

## Refactor-Prevention Rules
1. Add capabilities by implementing interfaces, not by changing cross-layer responsibilities.
2. Prefer additive fields and methods over changing existing shapes.
3. Introduce new modules behind existing contracts first, then wire in engine.
4. Keep all broker-specific fields confined to `execution` layer and scripts.
