from quantlab.execution.position_sizer import PositionSizer


def test_position_sizer_clamps_negative_target_when_short_disabled() -> None:
    sizer = PositionSizer()
    intents = sizer.size_orders(
        target_weights={"AAPL": -0.5},
        latest_prices={"AAPL": 100.0},
        equity=100000.0,
        current_positions={"AAPL": 99},
        allow_short=False,
    )

    assert len(intents) == 1
    assert intents[0].side == "sell"
    assert intents[0].quantity == 99
    assert intents[0].target_quantity == 0


def test_position_sizer_allows_negative_target_when_short_enabled() -> None:
    sizer = PositionSizer()
    intents = sizer.size_orders(
        target_weights={"AAPL": -0.5},
        latest_prices={"AAPL": 100.0},
        equity=100000.0,
        current_positions={"AAPL": 99},
        allow_short=True,
    )

    assert len(intents) == 1
    assert intents[0].side == "sell"
    assert intents[0].target_quantity < 0
    assert intents[0].quantity > 99
