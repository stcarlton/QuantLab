from datetime import datetime, timezone

from quantlab.db.models import OrderEventRecord, RebalanceRecord
from quantlab.db.repository import Repository
from quantlab.types import Bar


def test_sqlite_repository_query_helpers(tmp_path) -> None:
    db_path = tmp_path / "quantlab_repo.db"
    repository = Repository(db_path=str(db_path))

    repository.append_rebalance_record(
        RebalanceRecord(
            timestamp="2026-01-01T00:00:00+00:00",
            symbol="AAPL",
            execution_provider="paper_stub",
            equity_used=100000.0,
            signal_count=1,
            target_weights={"AAPL": 0.1},
            planned_order_count=1,
            submitted_order_count=0,
            skipped_due_to_open_orders=[],
            reconciled_terminal_order_count=0,
        )
    )
    repository.append_order_event(
        OrderEventRecord(
            timestamp="2026-01-01T00:01:00+00:00",
            order_id="order-1",
            status="filled",
            symbol="AAPL",
            filled_qty="1",
            filled_avg_price="100.0",
        )
    )

    rebalances = repository.query_recent_rebalances(limit=1)
    events = repository.query_recent_order_events(limit=1)

    assert len(rebalances) == 1
    assert rebalances[0].symbol == "AAPL"
    assert len(events) == 1
    assert events[0].order_id == "order-1"


def test_sqlite_repository_persists_market_bars(tmp_path) -> None:
    db_path = tmp_path / "quantlab_bars.db"
    repository = Repository(db_path=str(db_path))

    bars = [
        Bar(
            symbol="AAPL",
            timestamp=datetime(2026, 3, 3, 14, 30, tzinfo=timezone.utc),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            volume=1000.0,
        )
    ]
    repository.save_market_bars(bars, source="synthetic")
    recent = repository.query_recent_market_bars(limit=5, symbol="AAPL")

    assert len(recent) == 1
    assert recent[0].symbol == "AAPL"
    assert recent[0].close == 100.5
    assert recent[0].source == "synthetic"
