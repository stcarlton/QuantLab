from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from quantlab.config import Settings
from quantlab.data.loader import DataLoader, MissingBarDataError
from quantlab.db.models import OrderEventRecord, PortfolioState, RebalanceRecord
from quantlab.db.repository import Repository
from quantlab.execution.account_reconciler import equity_from_account
from quantlab.execution.alpaca_broker import AlpacaBroker
from quantlab.execution.broker_interface import BrokerInterface
from quantlab.execution.paper_executor import PaperExecutor
from quantlab.execution.position_reconciler import positions_from_broker
from quantlab.execution.position_sizer import PositionSizer
from quantlab.meta.allocator import Allocator
from quantlab.risk.risk_manager import RiskManager
from quantlab.strategies.momentum import MomentumStrategy
from quantlab.types import BlockedOrderIntent, OrderIntent, Signal
from quantlab.universe.selector import UniverseSelector


@dataclass(frozen=True)
class RunResult:
    symbol: str
    equity_used: float
    signal_count: int
    raw_weights: dict[str, float]
    target_weights: dict[str, float]
    planned_orders: list[OrderIntent]
    blocked_by_risk: list[BlockedOrderIntent]
    kill_switch_triggered: bool
    daily_loss_limit_triggered: bool
    skipped_due_to_open_orders: list[OrderIntent]
    orders_submitted: list[dict[str, Any]]
    reconciled_terminal_order_count: int
    submit_orders: bool
    execution_provider: str


class Engine:
    def __init__(
        self,
        settings: Settings,
        repository: Repository | None = None,
        execution: BrokerInterface | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository or Repository(
            db_path=settings.db_path,
            state_path=settings.state_path,
            rebalance_log_path=settings.rebalance_log_path,
            order_event_log_path=settings.order_event_log_path,
        )
        self.data_loader = DataLoader(
            source=settings.data_source,
            csv_path=settings.data_csv_path,
            alpaca_key_id=settings.alpaca_key_id,
            alpaca_secret_key=settings.alpaca_secret_key,
            alpaca_data_base_url=settings.alpaca_data_base_url,
            alpaca_data_mode=settings.alpaca_data_mode,
            alpaca_data_feed=settings.alpaca_data_feed,
            alpaca_data_timeframe=settings.alpaca_data_timeframe,
            alpaca_data_history_limit=settings.alpaca_data_history_limit,
            alpaca_data_history_start=settings.alpaca_data_history_start,
            alpaca_data_history_end=settings.alpaca_data_history_end,
            alpaca_stream_url=settings.alpaca_stream_url,
            alpaca_stream_wait_seconds=settings.alpaca_stream_wait_seconds,
        )
        self.strategy = MomentumStrategy()
        self.universe = UniverseSelector(settings)
        self.allocator = Allocator()
        self.risk = RiskManager(
            max_position_weight=settings.max_position_weight,
            max_gross_exposure=settings.max_gross_exposure,
            max_order_notional=settings.max_order_notional,
            daily_loss_limit_pct=settings.daily_loss_limit_pct,
            kill_switch=settings.kill_switch,
        )
        self.position_sizer = PositionSizer()
        self.execution = execution or self._build_execution_provider()

    def _build_execution_provider(self) -> BrokerInterface:
        if self.settings.execution_provider == "paper_stub":
            return PaperExecutor()
        if self.settings.execution_provider == "alpaca_paper":
            self.settings.require_alpaca_credentials()
            return AlpacaBroker(
                key_id=self.settings.alpaca_key_id or "",
                secret_key=self.settings.alpaca_secret_key or "",
                base_url=self.settings.alpaca_base_url,
            )
        raise ValueError(f"Unsupported execution provider: {self.settings.execution_provider}")

    def _bar_source_label(self) -> str:
        if self.settings.data_source == "alpaca":
            return f"alpaca:{self.settings.alpaca_data_mode}:{self.settings.alpaca_data_feed}"
        return self.settings.data_source

    def _reconcile_pending_orders(self, portfolio_state: PortfolioState) -> int:
        if self.settings.execution_provider != "alpaca_paper":
            return 0

        terminal_statuses = {"filled", "canceled", "rejected", "expired"}
        remaining_pending: list[str] = []
        terminal_count = 0

        for order_id in portfolio_state.pending_order_ids:
            order = self.execution.get_order(order_id)
            status = str(order.get("status", "")).lower()
            if status in terminal_statuses:
                terminal_count += 1
                self.repository.append_order_event(
                    OrderEventRecord(
                        timestamp=datetime.now(tz=timezone.utc).isoformat(),
                        order_id=order_id,
                        status=status,
                        symbol=order.get("symbol") if isinstance(order.get("symbol"), str) else None,
                        filled_qty=str(order.get("filled_qty")) if order.get("filled_qty") is not None else None,
                        filled_avg_price=(
                            str(order.get("filled_avg_price")) if order.get("filled_avg_price") is not None else None
                        ),
                    )
                )
            else:
                remaining_pending.append(order_id)

        portfolio_state.pending_order_ids = remaining_pending
        return terminal_count

    def reconcile_orders_once(self) -> int:
        portfolio_state = self.repository.load_portfolio_state()
        reconciled_terminal_order_count = self._reconcile_pending_orders(portfolio_state)
        self.repository.save_portfolio_state(portfolio_state)
        return reconciled_terminal_order_count

    def run_once(self) -> RunResult:
        portfolio_state = self.repository.load_portfolio_state()
        reconciled_terminal_order_count = self._reconcile_pending_orders(portfolio_state)
        equity_used = self.settings.starting_cash
        if self.settings.execution_provider == "alpaca_paper":
            broker_positions = self.execution.list_positions()
            portfolio_state.current_positions = positions_from_broker(broker_positions)
            account = self.execution.get_account()
            equity_used = equity_from_account(account, fallback_equity=self.settings.starting_cash)

        symbols = self.universe.select()
        all_bars = []
        latest_prices: dict[str, float] = {}
        skipped_symbols_no_data: list[str] = []
        for symbol in symbols:
            try:
                bars = self.data_loader.load_bars(symbol)
            except MissingBarDataError:
                skipped_symbols_no_data.append(symbol)
                continue
            all_bars.extend(bars)
            if bars:
                latest_prices[symbol] = bars[-1].close

        if not all_bars:
            universe_preview = ",".join(symbols[:10])
            if len(symbols) > 10:
                universe_preview += ",..."
            raise ValueError(
                "No market bars were loaded for the selected universe. "
                f"Attempted symbols: {universe_preview}. "
                "If using Alpaca assets with feed=iex, switch to static universe "
                "(e.g. QL_UNIVERSE_MODE=static, QL_SYMBOL=AAPL) or use a compatible feed."
            )

        self.repository.save_market_bars(all_bars, source=self._bar_source_label())
        signals: list[Signal] = []
        for bar in all_bars:
            signal = self.strategy.on_bar(bar)
            if signal is not None:
                signals.append(signal)

        raw_weights = self.allocator.allocate(signals)
        target_weights = self.risk.validate_target_weights(raw_weights)
        planned_orders = self.position_sizer.size_orders(
            target_weights=target_weights,
            latest_prices=latest_prices,
            equity=equity_used,
            current_positions=portfolio_state.current_positions,
            allow_short=self.settings.allow_short,
        )
        approved_orders, blocked_by_risk, kill_switch_triggered, daily_loss_limit_triggered = self.risk.filter_order_intents(
            planned_orders,
            equity_used=equity_used,
            starting_cash=self.settings.starting_cash,
        )

        submitted_orders: list[dict[str, Any]] = []
        skipped_due_to_open_orders: list[OrderIntent] = []
        if self.settings.submit_orders:
            open_orders = self.execution.list_open_orders()
            open_order_symbols = {
                str(order.get("symbol"))
                for order in open_orders
                if isinstance(order.get("symbol"), str)
            }

            for intent in approved_orders:
                if intent.symbol in open_order_symbols:
                    skipped_due_to_open_orders.append(intent)
                    continue
                order = self.execution.submit_order(
                    symbol=intent.symbol,
                    quantity=float(intent.quantity),
                    side=intent.side,
                )
                submitted_orders.append(order)
                if self.settings.execution_provider == "alpaca_paper":
                    order_id = order.get("id")
                    if isinstance(order_id, str):
                        portfolio_state.pending_order_ids.append(order_id)

            if self.settings.execution_provider == "paper_stub":
                updated_positions = dict(portfolio_state.current_positions)
                for intent in approved_orders:
                    if intent in skipped_due_to_open_orders:
                        continue
                    updated_positions[intent.symbol] = intent.target_quantity
                portfolio_state.current_positions = updated_positions

        portfolio_state.last_target_weights = target_weights
        run_timestamp = datetime.now(tz=timezone.utc).isoformat()
        portfolio_state.last_rebalance_at = run_timestamp
        self.repository.save_portfolio_state(portfolio_state)
        self.repository.append_rebalance_record(
            RebalanceRecord(
                timestamp=run_timestamp,
                symbol=self.settings.symbol,
                execution_provider=self.settings.execution_provider,
                equity_used=equity_used,
                signal_count=len(signals),
                target_weights=target_weights,
                planned_order_count=len(planned_orders),
                submitted_order_count=len(submitted_orders),
                skipped_due_to_open_orders=[intent.symbol for intent in skipped_due_to_open_orders],
                reconciled_terminal_order_count=reconciled_terminal_order_count,
            )
        )

        return RunResult(
            symbol=self.settings.symbol,
            equity_used=equity_used,
            signal_count=len(signals),
            raw_weights=raw_weights,
            target_weights=target_weights,
            planned_orders=planned_orders,
            blocked_by_risk=blocked_by_risk,
            kill_switch_triggered=kill_switch_triggered,
            daily_loss_limit_triggered=daily_loss_limit_triggered,
            skipped_due_to_open_orders=skipped_due_to_open_orders,
            orders_submitted=submitted_orders,
            reconciled_terminal_order_count=reconciled_terminal_order_count,
            submit_orders=self.settings.submit_orders,
            execution_provider=self.settings.execution_provider,
        )

    def run(self) -> None:
        result = self.run_once()
        print(f"Engine run completed for symbol={result.symbol}")
        print(f"Signals generated: {result.signal_count}")
        print(f"Equity used for sizing: {result.equity_used}")
        print(f"Raw target weights: {result.raw_weights}")
        print(f"Risk-adjusted target weights: {result.target_weights}")
        print(f"Planned orders: {len(result.planned_orders)}")
        print(f"Blocked by risk: {len(result.blocked_by_risk)}")
        print(f"Kill switch triggered: {result.kill_switch_triggered}")
        print(f"Daily loss limit triggered: {result.daily_loss_limit_triggered}")
        print(f"Skipped due to open orders: {len(result.skipped_due_to_open_orders)}")
        print(f"Reconciled terminal orders: {result.reconciled_terminal_order_count}")
        print(f"Execution provider: {result.execution_provider}")
        if result.submit_orders:
            print(f"Orders submitted: {len(result.orders_submitted)}")
        else:
            print("Orders submitted: 0 (submit_orders=false)")
