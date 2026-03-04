from quantlab.execution.position_reconciler import positions_from_broker


def test_positions_from_broker_parses_qty_and_ignores_invalid_rows() -> None:
    raw = [
        {"symbol": "AAPL", "qty": "3"},
        {"symbol": "TSLA", "qty": "-2"},
        {"symbol": "MSFT", "qty": "1.9"},
        {"symbol": "NVDA", "qty": "not-a-number"},
        {"symbol": 123, "qty": "5"},
    ]

    result = positions_from_broker(raw)

    assert result == {
        "AAPL": 3,
        "TSLA": -2,
        "MSFT": 1,
    }
