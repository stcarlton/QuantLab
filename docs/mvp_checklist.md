# MVP Checklist

## Objective
Deliver a reliable paper-trading MVP with deterministic behavior, clear operational visibility, and minimal manual intervention.

## Status Summary
- [x] Engine orchestration path (`data -> strategy -> meta -> risk -> execution`)
- [x] Delta-based position sizing
- [x] Broker position reconciliation (`alpaca_paper`)
- [x] Broker equity reconciliation (`alpaca_paper`)
- [x] Open-order duplicate protection
- [x] Rebalance JSONL logging
- [x] Config-driven data source (`synthetic`, `csv`)

## Remaining MVP Work
1. **Execution Reconciliation**
- [x] Persist submitted order ids and reconcile terminal status/fills into portfolio state.
- [x] Add periodic reconciliation script/job.

2. **Run Loop**
- [x] Add non-blocking scheduler wrapper for repeated `run_once()` execution.
- [x] Add configurable cadence and graceful shutdown handling.

3. **Persistence Upgrade**
- [x] Move state/log artifacts from JSON files to SQLite tables.
- [x] Add query helpers for recent runs, open intents, and fill history.

4. **Risk v1**
- [x] Add max order notional guard.
- [x] Add daily loss cap guard.
- [x] Add kill-switch toggle.

5. **Operational Tooling**
- [x] Add script to list current engine state snapshot.
- [x] Add safe cancel-open-orders script for paper mode.

6. **Testing Expansion**
- [ ] Integration test for CSV-backed engine run.
- [ ] Integration test for order reconciliation transitions.
- [ ] Failure-mode tests for transient broker API errors.

## Next Recommended Step
Implement **Testing Expansion** first, starting with a CSV-backed integration run and transient broker failure-path tests.
