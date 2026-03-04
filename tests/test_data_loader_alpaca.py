import json

from quantlab.data.loader import DataLoader


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._body


def test_data_loader_alpaca_latest(monkeypatch) -> None:
    payload = {
        "bars": {
            "AAPL": {
                "t": "2026-03-03T14:30:00Z",
                "o": 180.0,
                "h": 181.0,
                "l": 179.5,
                "c": 180.5,
                "v": 12345,
            }
        }
    }

    def fake_urlopen(req, timeout=20):  # noqa: ANN001
        _ = req, timeout
        return _FakeResponse(payload)

    monkeypatch.setattr("quantlab.data.loader.request.urlopen", fake_urlopen)

    loader = DataLoader(
        source="alpaca",
        alpaca_key_id="k",
        alpaca_secret_key="s",
        alpaca_data_mode="latest",
        alpaca_data_feed="iex",
    )
    bars = loader.load_bars("AAPL")

    assert len(bars) == 1
    assert bars[0].symbol == "AAPL"
    assert bars[0].close == 180.5


def test_data_loader_alpaca_historical(monkeypatch) -> None:
    payload = {
        "bars": [
            {"t": "2026-03-03T14:30:00Z", "o": 100, "h": 101, "l": 99, "c": 100.5, "v": 1000},
            {"t": "2026-03-03T14:31:00Z", "o": 100.5, "h": 101.2, "l": 100.2, "c": 101.0, "v": 1200},
        ]
    }

    def fake_urlopen(req, timeout=20):  # noqa: ANN001
        _ = req, timeout
        return _FakeResponse(payload)

    monkeypatch.setattr("quantlab.data.loader.request.urlopen", fake_urlopen)

    loader = DataLoader(
        source="alpaca",
        alpaca_key_id="k",
        alpaca_secret_key="s",
        alpaca_data_mode="historical",
        alpaca_data_timeframe="1Min",
    )
    bars = loader.load_bars("AAPL")

    assert len(bars) == 2
    assert bars[-1].close == 101.0


def test_data_loader_alpaca_requires_credentials() -> None:
    loader = DataLoader(source="alpaca", alpaca_data_mode="latest")
    try:
        loader.load_bars("AAPL")
        assert False, "Expected missing credentials error"
    except ValueError as exc:
        assert "Missing Alpaca credentials" in str(exc)


def test_data_loader_alpaca_stream_returns_cached_latest_bar(monkeypatch) -> None:
    loader = DataLoader(
        source="alpaca",
        alpaca_key_id="k",
        alpaca_secret_key="s",
        alpaca_data_mode="stream",
        alpaca_stream_wait_seconds=1,
    )

    def fake_ensure_stream(symbol: str) -> None:
        _ = symbol
        loader._latest_stream_bar = loader._bar_from_alpaca_stream(  # type: ignore[attr-defined]
            {
                "T": "b",
                "S": "AAPL",
                "t": "2026-03-03T14:30:00Z",
                "o": 180.0,
                "h": 181.0,
                "l": 179.5,
                "c": 180.5,
                "v": 12345,
            }
        )
        loader._stream_ready.set()  # type: ignore[attr-defined]

    monkeypatch.setattr(loader, "_ensure_stream", fake_ensure_stream)
    bars = loader.load_bars("AAPL")

    assert len(bars) == 1
    assert bars[0].symbol == "AAPL"
    assert bars[0].close == 180.5


def test_data_loader_alpaca_stream_times_out(monkeypatch) -> None:
    loader = DataLoader(
        source="alpaca",
        alpaca_key_id="k",
        alpaca_secret_key="s",
        alpaca_data_mode="stream",
        alpaca_stream_wait_seconds=1,
    )
    monkeypatch.setattr(loader, "_ensure_stream", lambda symbol: None)
    monkeypatch.setattr(
        loader,
        "_load_alpaca_latest",
        lambda symbol: [
            loader._bar_from_alpaca(  # type: ignore[attr-defined]
                symbol=symbol,
                payload={
                    "t": "2026-03-03T14:30:00Z",
                    "o": 180.0,
                    "h": 181.0,
                    "l": 179.5,
                    "c": 180.5,
                    "v": 12345,
                },
            )
        ],
    )

    bars = loader.load_bars("AAPL")
    assert len(bars) == 1
    assert bars[0].close == 180.5
