from quantlab.config import Settings
from quantlab.universe.selector import UniverseSelector


def test_universe_selector_static_uses_symbols_csv() -> None:
    settings = Settings(
        universe_mode="static",
        symbols_csv="AAPL, msft, SPY",
        symbol="NVDA",
    )
    symbols = UniverseSelector(settings).select()
    assert symbols == ["AAPL", "MSFT", "SPY"]


def test_universe_selector_static_falls_back_to_symbol() -> None:
    settings = Settings(
        universe_mode="static",
        symbols_csv=None,
        symbol="tsla",
    )
    symbols = UniverseSelector(settings).select()
    assert symbols == ["TSLA"]
