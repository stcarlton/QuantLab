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


def test_universe_selector_alpaca_assets_ranks_by_dollar_volume(monkeypatch) -> None:
    settings = Settings(
        universe_mode="alpaca_assets",
        universe_limit=2,
        alpaca_key_id="key",
        alpaca_secret_key="secret",
    )
    selector = UniverseSelector(settings)

    monkeypatch.setattr(
        selector,
        "_fetch_alpaca_most_actives",
        lambda top: ["MSFT", "SPY", "AAPL", "BRK.B"],
    )

    symbols = selector.select()
    assert symbols == ["MSFT", "SPY"]


def test_universe_selector_alpaca_assets_fallback_ranks_and_caches(monkeypatch) -> None:
    settings = Settings(
        universe_mode="alpaca_assets",
        universe_limit=10,
        alpaca_key_id="key",
        alpaca_secret_key="secret",
    )
    selector = UniverseSelector(settings)

    call_count = {"snapshots": 0, "most_actives": 0}

    def _fail_most_actives(top: int) -> list[str]:
        call_count["most_actives"] += 1
        raise RuntimeError("screener unavailable")

    monkeypatch.setattr(selector, "_fetch_alpaca_most_actives", _fail_most_actives)

    monkeypatch.setattr(
        selector,
        "_fetch_alpaca_assets",
        lambda: [
            {"symbol": "AAPL", "tradable": True, "shortable": True, "exchange": "NASDAQ"},
            {"symbol": "MSFT", "tradable": True, "shortable": True, "exchange": "NASDAQ"},
            {"symbol": "OTCM", "tradable": True, "shortable": True, "exchange": "OTC"},
            {"symbol": "XYZ", "tradable": False, "shortable": True, "exchange": "NASDAQ"},
        ],
    )

    def _fake_snapshots(symbols: list[str]) -> dict[str, dict[str, dict[str, float]]]:
        call_count["snapshots"] += 1
        return {
            "AAPL": {"dailyBar": {"c": 100.0, "v": 1_000_000}},
            "MSFT": {"dailyBar": {"c": 400.0, "v": 5_000_000}},
        }

    monkeypatch.setattr(selector, "_fetch_snapshots_for_symbols", _fake_snapshots)

    first = selector.select()
    second = selector.select()

    assert first == ["MSFT", "AAPL"]
    assert second == ["MSFT", "AAPL"]
    assert call_count["most_actives"] == 1
    assert call_count["snapshots"] == 1
