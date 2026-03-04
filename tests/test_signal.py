from datetime import datetime

from quantlab.types import Signal


def test_signal_shape() -> None:
    signal = Signal(
        strategy_id="s1",
        symbol="AAPL",
        direction="long",
        confidence=0.9,
        timestamp=datetime(2026, 1, 1),
    )

    assert signal.strategy_id == "s1"
