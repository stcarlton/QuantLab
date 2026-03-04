from typing import Any, Literal

from quantlab.config import Settings
from quantlab.db.models import PortfolioState
from quantlab.db.repository import Repository
from quantlab.engine import Engine
from quantlab.execution.broker_interface import BrokerInterface
from quantlab.types import Bar, Signal
from datetime import datetime, timezone


class FakeOpenOrderBroker(BrokerInterface):
    def submit_order(
        self,
        symbol: str,
        quantity: float,
        side: Literal["buy", "sell"] = "buy",
        order_type: Literal["market"] = "market",
        time_in_force: Literal["day", "gtc"] = "day",
    ) -> dict[str, Any]:
        return {"symbol": symbol, "qty": quantity, "side": side, "status": "accepted"}

    def get_account(self) -> dict[str, Any]:
        return {}

    def get_order(self, order_id: str) -> dict[str, Any]:
        return {}

    def list_open_orders(self) -> list[dict[str, Any]]:
        return [{"symbol": "AAPL"}]

    def list_positions(self) -> list[dict[str, Any]]:
        return []

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        return {"id": order_id, "status": "canceled"}

    def cancel_all_open_orders(self) -> list[dict[str, Any]]:
        return []


class FakeAlpacaBroker(BrokerInterface):
    def __init__(self) -> None:
        self.submitted_order_ids: list[str] = []

    def submit_order(
        self,
        symbol: str,
        quantity: float,
        side: Literal["buy", "sell"] = "buy",
        order_type: Literal["market"] = "market",
        time_in_force: Literal["day", "gtc"] = "day",
    ) -> dict[str, Any]:
        order_id = f"order-{len(self.submitted_order_ids) + 1}"
        self.submitted_order_ids.append(order_id)
        return {"id": order_id, "symbol": symbol, "qty": quantity, "side": side, "status": "accepted"}

    def get_account(self) -> dict[str, Any]:
        return {"equity": "50000"}

    def get_order(self, order_id: str) -> dict[str, Any]:
        return {
            "id": order_id,
            "symbol": "AAPL",
            "status": "filled",
            "filled_qty": "39",
            "filled_avg_price": "100.80",
        }

    def list_open_orders(self) -> list[dict[str, Any]]:
        return []

    def list_positions(self) -> list[dict[str, Any]]:
        return [{"symbol": "AAPL", "qty": "10"}]

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        return {"id": order_id, "status": "canceled"}

    def cancel_all_open_orders(self) -> list[dict[str, Any]]:
        return []


class FakeLossAlpacaBroker(FakeAlpacaBroker):
    def get_account(self) -> dict[str, Any]:
        return {"equity": "80000"}


class FakeDataLoaderOneBar:
    def load_bars(self, symbol: str) -> list[Bar]:
        return [
            Bar(
                symbol=symbol,
                timestamp=datetime(2026, 3, 3, 14, 30, tzinfo=timezone.utc),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000.0,
            )
        ]


class FakeDataLoaderBySymbol:
    def load_bars(self, symbol: str) -> list[Bar]:
        if symbol == "AAPL":
            open_price = 100.0
            close_price = 101.0
        else:
            open_price = 200.0
            close_price = 201.0
        return [
            Bar(
                symbol=symbol,
                timestamp=datetime(2026, 3, 3, 14, 30, tzinfo=timezone.utc),
                open=open_price,
                high=close_price + 1.0,
                low=open_price - 1.0,
                close=close_price,
                volume=1000.0,
            )
        ]


class FakeShortStrategy:
    strategy_id = "short_test"

    def on_bar(self, bar: Bar) -> Signal | None:
        return Signal(
            strategy_id=self.strategy_id,
            symbol=bar.symbol,
            direction="short",
            confidence=1.0,
            timestamp=bar.timestamp,
        )


def test_engine_run_once_full_path_without_submitting_orders(tmp_path) -> None:
    db_path = tmp_path / "quantlab_no_submit.db"
    settings = Settings(
        symbol="AAPL",
        execution_provider="paper_stub",
        submit_orders=False,
        db_path=str(db_path),
    )

    repository = Repository(db_path=str(db_path))
    result = Engine(settings, repository=repository).run_once()

    assert result.symbol == "AAPL"
    assert result.signal_count == 1
    assert "AAPL" in result.raw_weights
    assert "AAPL" in result.target_weights
    assert len(result.planned_orders) == 1
    assert result.planned_orders[0].symbol == "AAPL"
    assert result.planned_orders[0].side == "buy"
    assert result.planned_orders[0].quantity == 99
    assert result.planned_orders[0].current_quantity == 0
    assert result.planned_orders[0].target_quantity == 99
    assert result.skipped_due_to_open_orders == []
    assert result.orders_submitted == []
    assert result.blocked_by_risk == []
    assert result.kill_switch_triggered is False
    assert result.daily_loss_limit_triggered is False
    assert result.execution_provider == "paper_stub"
    recent_bars = repository.query_recent_market_bars(limit=5, symbol="AAPL")
    assert len(recent_bars) == 1
    assert recent_bars[0].source == "synthetic"


def test_engine_delta_sizing_uses_saved_positions(tmp_path) -> None:
    db_path = tmp_path / "quantlab_delta.db"
    settings = Settings(
        symbol="AAPL",
        execution_provider="paper_stub",
        submit_orders=True,
        db_path=str(db_path),
    )
    engine = Engine(settings)

    first_result = engine.run_once()
    assert len(first_result.planned_orders) == 1
    assert first_result.planned_orders[0].quantity == 99
    assert first_result.skipped_due_to_open_orders == []
    assert len(first_result.orders_submitted) == 1

    second_result = engine.run_once()
    assert second_result.planned_orders == []


def test_engine_skips_submission_when_open_order_exists(tmp_path) -> None:
    db_path = tmp_path / "quantlab_open_order.db"
    settings = Settings(
        symbol="AAPL",
        execution_provider="paper_stub",
        submit_orders=True,
        db_path=str(db_path),
    )

    engine = Engine(settings, execution=FakeOpenOrderBroker())
    result = engine.run_once()

    assert len(result.planned_orders) == 1
    assert len(result.orders_submitted) == 0
    assert len(result.skipped_due_to_open_orders) == 1
    assert result.skipped_due_to_open_orders[0].symbol == "AAPL"


def test_engine_writes_rebalance_log(tmp_path) -> None:
    db_path = tmp_path / "quantlab_rebalance.db"
    settings = Settings(
        symbol="AAPL",
        execution_provider="paper_stub",
        submit_orders=False,
        db_path=str(db_path),
    )
    repository = Repository(db_path=str(db_path))
    Engine(settings, repository=repository).run_once()
    records = repository.query_recent_rebalances(limit=1)
    assert len(records) == 1
    assert records[0].symbol == "AAPL"
    assert records[0].planned_order_count == 1


def test_engine_uses_broker_equity_and_positions_for_alpaca_mode(tmp_path) -> None:
    db_path = tmp_path / "quantlab_alpaca.db"
    settings = Settings(
        symbol="AAPL",
        execution_provider="alpaca_paper",
        submit_orders=False,
        db_path=str(db_path),
    )

    result = Engine(settings, execution=FakeAlpacaBroker()).run_once()

    assert result.equity_used == 50000.0
    assert len(result.planned_orders) == 1
    # Target qty floor(0.1 * 50000 / 100.8) = 49, current qty = 10, delta = 39 buy.
    assert result.planned_orders[0].current_quantity == 10
    assert result.planned_orders[0].target_quantity == 49
    assert result.planned_orders[0].quantity == 39
    assert result.planned_orders[0].side == "buy"


def test_engine_reconciles_pending_alpaca_orders(tmp_path) -> None:
    db_path = tmp_path / "quantlab_pending.db"
    settings = Settings(
        symbol="AAPL",
        execution_provider="alpaca_paper",
        submit_orders=True,
        db_path=str(db_path),
    )
    repository = Repository(db_path=str(db_path))
    broker = FakeAlpacaBroker()
    engine = Engine(settings, repository=repository, execution=broker)

    first = engine.run_once()
    assert len(first.orders_submitted) == 1
    assert first.reconciled_terminal_order_count == 0

    second = engine.run_once()
    assert second.reconciled_terminal_order_count == 1
    events = repository.query_recent_order_events(limit=5)
    assert len(events) == 1
    assert events[0].status == "filled"


def test_reconcile_orders_once_clears_pending_without_full_run(tmp_path) -> None:
    db_path = tmp_path / "quantlab_reconcile_only.db"
    repository = Repository(db_path=str(db_path))
    repository.save_portfolio_state(PortfolioState(pending_order_ids=["order-42"]))

    settings = Settings(
        symbol="AAPL",
        execution_provider="alpaca_paper",
        submit_orders=False,
        db_path=str(db_path),
    )
    engine = Engine(settings, repository=repository, execution=FakeAlpacaBroker())

    reconciled = engine.reconcile_orders_once()
    assert reconciled == 1

    state = repository.load_portfolio_state()
    assert state.pending_order_ids == []
    events = repository.query_recent_order_events(limit=1)
    assert len(events) == 1


def test_engine_blocks_orders_when_max_notional_exceeded(tmp_path) -> None:
    db_path = tmp_path / "quantlab_max_notional.db"
    settings = Settings(
        symbol="AAPL",
        execution_provider="paper_stub",
        submit_orders=True,
        max_order_notional=1000.0,
        db_path=str(db_path),
    )

    result = Engine(settings).run_once()

    assert len(result.planned_orders) == 1
    assert len(result.blocked_by_risk) == 1
    assert result.blocked_by_risk[0].reason == "max_order_notional"
    assert result.orders_submitted == []


def test_engine_blocks_orders_when_kill_switch_enabled(tmp_path) -> None:
    db_path = tmp_path / "quantlab_killswitch.db"
    settings = Settings(
        symbol="AAPL",
        execution_provider="paper_stub",
        submit_orders=True,
        kill_switch=True,
        db_path=str(db_path),
    )

    result = Engine(settings).run_once()

    assert len(result.planned_orders) == 1
    assert len(result.blocked_by_risk) == 1
    assert result.blocked_by_risk[0].reason == "kill_switch"
    assert result.kill_switch_triggered is True
    assert result.orders_submitted == []


def test_engine_blocks_orders_on_daily_loss_limit(tmp_path) -> None:
    db_path = tmp_path / "quantlab_daily_loss.db"
    settings = Settings(
        symbol="AAPL",
        execution_provider="alpaca_paper",
        submit_orders=True,
        daily_loss_limit_pct=0.10,
        db_path=str(db_path),
    )

    result = Engine(settings, execution=FakeLossAlpacaBroker()).run_once()

    assert len(result.planned_orders) == 1
    assert len(result.blocked_by_risk) == 1
    assert result.blocked_by_risk[0].reason == "daily_loss_limit"
    assert result.daily_loss_limit_triggered is True
    assert result.orders_submitted == []


def test_engine_does_not_submit_cross_zero_short_when_short_disabled(tmp_path) -> None:
    db_path = tmp_path / "quantlab_no_cross_short.db"
    repository = Repository(db_path=str(db_path))
    repository.save_portfolio_state(PortfolioState(current_positions={"AAPL": 99}))

    settings = Settings(
        symbol="AAPL",
        execution_provider="paper_stub",
        submit_orders=True,
        allow_short=False,
        db_path=str(db_path),
    )
    engine = Engine(settings)
    engine.repository = repository
    engine.data_loader = FakeDataLoaderOneBar()
    engine.strategy = FakeShortStrategy()

    result = engine.run_once()

    assert len(result.planned_orders) == 1
    assert result.planned_orders[0].side == "sell"
    assert result.planned_orders[0].quantity == 99
    assert result.planned_orders[0].target_quantity == 0
    assert len(result.orders_submitted) == 1


def test_engine_processes_static_multi_symbol_universe(tmp_path) -> None:
    db_path = tmp_path / "quantlab_multi_symbol.db"
    settings = Settings(
        symbol="AAPL",
        symbols_csv="AAPL,MSFT",
        universe_mode="static",
        execution_provider="paper_stub",
        submit_orders=False,
        db_path=str(db_path),
    )
    repository = Repository(db_path=str(db_path))
    engine = Engine(settings, repository=repository)
    engine.data_loader = FakeDataLoaderBySymbol()

    result = engine.run_once()

    assert result.signal_count == 2
    assert "AAPL" in result.target_weights
    assert "MSFT" in result.target_weights
    bars = repository.query_recent_market_bars(limit=10)
    symbols = {bar.symbol for bar in bars}
    assert "AAPL" in symbols
    assert "MSFT" in symbols
