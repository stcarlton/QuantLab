"""Data loading interfaces."""

import csv
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib import parse, request

from quantlab.types import Bar


class DataLoader:
    def __init__(
        self,
        source: Literal["synthetic", "csv", "alpaca"] = "synthetic",
        csv_path: str | None = None,
        alpaca_key_id: str | None = None,
        alpaca_secret_key: str | None = None,
        alpaca_data_base_url: str = "https://data.alpaca.markets",
        alpaca_data_mode: Literal["latest", "historical", "stream"] = "latest",
        alpaca_data_feed: str = "iex",
        alpaca_data_timeframe: str = "1Min",
        alpaca_data_history_limit: int = 100,
        alpaca_data_history_start: str | None = None,
        alpaca_data_history_end: str | None = None,
        alpaca_stream_url: str = "wss://stream.data.alpaca.markets",
        alpaca_stream_wait_seconds: int = 10,
    ) -> None:
        self.source = source
        self.csv_path = csv_path
        self.alpaca_key_id = alpaca_key_id
        self.alpaca_secret_key = alpaca_secret_key
        self.alpaca_data_base_url = alpaca_data_base_url.rstrip("/")
        self.alpaca_data_mode = alpaca_data_mode
        self.alpaca_data_feed = alpaca_data_feed
        self.alpaca_data_timeframe = alpaca_data_timeframe
        self.alpaca_data_history_limit = max(1, alpaca_data_history_limit)
        self.alpaca_data_history_start = alpaca_data_history_start
        self.alpaca_data_history_end = alpaca_data_history_end
        self.alpaca_stream_url = alpaca_stream_url.rstrip("/")
        self.alpaca_stream_wait_seconds = max(1, alpaca_stream_wait_seconds)
        self._stream_symbol: str | None = None
        self._stream_thread: threading.Thread | None = None
        self._stream_stop = threading.Event()
        self._stream_ready = threading.Event()
        self._stream_lock = threading.Lock()
        self._latest_stream_bar: Bar | None = None

    def _parse_ts(self, raw: str) -> datetime:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts

    def _bar_from_alpaca(self, symbol: str, payload: dict[str, Any]) -> Bar:
        return Bar(
            symbol=symbol,
            timestamp=self._parse_ts(str(payload["t"])),
            open=float(payload["o"]),
            high=float(payload["h"]),
            low=float(payload["l"]),
            close=float(payload["c"]),
            volume=float(payload["v"]),
        )

    def _bar_from_alpaca_stream(self, payload: dict[str, Any]) -> Bar:
        symbol = str(payload["S"])
        return Bar(
            symbol=symbol,
            timestamp=self._parse_ts(str(payload["t"])),
            open=float(payload["o"]),
            high=float(payload["h"]),
            low=float(payload["l"]),
            close=float(payload["c"]),
            volume=float(payload["v"]),
        )

    def _alpaca_headers(self) -> dict[str, str]:
        if not self.alpaca_key_id or not self.alpaca_secret_key:
            raise ValueError("Missing Alpaca credentials for data loading.")
        return {
            "APCA-API-KEY-ID": self.alpaca_key_id,
            "APCA-API-SECRET-KEY": self.alpaca_secret_key,
        }

    def _alpaca_get_json(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        query = parse.urlencode(params)
        req = request.Request(
            url=f"{self.alpaca_data_base_url}{path}?{query}",
            headers=self._alpaca_headers(),
            method="GET",
        )
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise RuntimeError("Unexpected Alpaca data response format.")
            return payload

    def _load_alpaca_latest(self, symbol: str) -> list[Bar]:
        payload = self._alpaca_get_json(
            path="/v2/stocks/bars/latest",
            params={
                "symbols": symbol,
                "feed": self.alpaca_data_feed,
            },
        )
        bars = payload.get("bars", {})
        if not isinstance(bars, dict) or symbol not in bars:
            raise ValueError(f"No latest Alpaca bar for symbol '{symbol}'.")
        row = bars[symbol]
        if not isinstance(row, dict):
            raise RuntimeError("Unexpected latest bar payload.")
        return [self._bar_from_alpaca(symbol=symbol, payload=row)]

    def _load_alpaca_historical(self, symbol: str) -> list[Bar]:
        params = {
            "timeframe": self.alpaca_data_timeframe,
            "feed": self.alpaca_data_feed,
            "limit": str(self.alpaca_data_history_limit),
        }
        if self.alpaca_data_history_start:
            params["start"] = self.alpaca_data_history_start
        if self.alpaca_data_history_end:
            params["end"] = self.alpaca_data_history_end

        payload = self._alpaca_get_json(
            path=f"/v2/stocks/{symbol}/bars",
            params=params,
        )
        rows = payload.get("bars", [])
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"No historical Alpaca bars for symbol '{symbol}'.")

        bars: list[Bar] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            bars.append(self._bar_from_alpaca(symbol=symbol, payload=row))

        if not bars:
            raise ValueError(f"No parseable historical Alpaca bars for symbol '{symbol}'.")
        return bars

    def _stream_worker(self, symbol: str) -> None:
        try:
            import websocket  # type: ignore
        except ImportError as exc:
            raise RuntimeError("websocket-client is required for Alpaca stream mode.") from exc

        ws_url = f"{self.alpaca_stream_url}/v2/{self.alpaca_data_feed}"
        while not self._stream_stop.is_set():
            ws = None
            try:
                ws = websocket.create_connection(ws_url, timeout=20)
                ws.send(
                    json.dumps(
                        {
                            "action": "auth",
                            "key": self.alpaca_key_id,
                            "secret": self.alpaca_secret_key,
                        }
                    )
                )
                ws.send(json.dumps({"action": "subscribe", "bars": [symbol]}))

                while not self._stream_stop.is_set():
                    raw = ws.recv()
                    if not raw:
                        continue
                    payload = json.loads(raw)
                    messages = payload if isinstance(payload, list) else [payload]
                    for message in messages:
                        if not isinstance(message, dict):
                            continue
                        if message.get("T") != "b":
                            continue
                        if message.get("S") != symbol:
                            continue
                        bar = self._bar_from_alpaca_stream(message)
                        with self._stream_lock:
                            self._latest_stream_bar = bar
                        self._stream_ready.set()
            except Exception:
                # Keep reconnecting for resilient stream ingestion.
                if not self._stream_stop.is_set():
                    time.sleep(1.0)
            finally:
                if ws is not None:
                    try:
                        ws.close()
                    except Exception:
                        pass

    def _stop_stream_thread(self) -> None:
        self._stream_stop.set()
        if self._stream_thread is not None and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=2)
        self._stream_thread = None
        self._stream_stop = threading.Event()
        self._stream_ready = threading.Event()
        with self._stream_lock:
            self._latest_stream_bar = None

    def _ensure_stream(self, symbol: str) -> None:
        if symbol != self._stream_symbol:
            self._stop_stream_thread()
            self._stream_symbol = symbol

        if self._stream_thread is None or not self._stream_thread.is_alive():
            self._stream_thread = threading.Thread(
                target=self._stream_worker,
                args=(symbol,),
                daemon=True,
            )
            self._stream_thread.start()

    def _load_alpaca_stream(self, symbol: str) -> list[Bar]:
        if not self.alpaca_key_id or not self.alpaca_secret_key:
            raise ValueError("Missing Alpaca credentials for data loading.")

        self._ensure_stream(symbol)
        ready = self._stream_ready.wait(timeout=self.alpaca_stream_wait_seconds)
        if not ready:
            # Quiet periods can produce sparse stream bars; fall back to latest REST bar.
            return self._load_alpaca_latest(symbol)

        with self._stream_lock:
            if self._latest_stream_bar is None:
                raise RuntimeError("Stream ready but no bar cached.")
            return [self._latest_stream_bar]

    def _load_synthetic(self, symbol: str) -> list[Bar]:
        return [
            Bar(
                symbol=symbol,
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                open=100.0,
                high=101.0,
                low=99.5,
                close=100.8,
                volume=100_000.0,
            )
        ]

    def _load_from_csv(self, symbol: str) -> list[Bar]:
        if not self.csv_path:
            raise ValueError("CSV data source selected but QL_DATA_CSV_PATH is not set.")

        path = Path(self.csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV data file not found: {path}")

        bars: list[Bar] = []
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_symbol = (row.get("symbol") or symbol).strip()
                if row_symbol != symbol:
                    continue

                timestamp_raw = (row.get("timestamp") or "").strip()
                if not timestamp_raw:
                    continue
                timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))

                bars.append(
                    Bar(
                        symbol=row_symbol,
                        timestamp=timestamp,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row["volume"]),
                    )
                )

        if not bars:
            raise ValueError(f"No bars found in {path} for symbol '{symbol}'.")
        return bars

    def load_bars(self, symbol: str) -> list[Bar]:
        if self.source == "synthetic":
            return self._load_synthetic(symbol)
        if self.source == "csv":
            return self._load_from_csv(symbol)
        if self.source == "alpaca":
            if self.alpaca_data_mode == "latest":
                return self._load_alpaca_latest(symbol)
            if self.alpaca_data_mode == "historical":
                return self._load_alpaca_historical(symbol)
            if self.alpaca_data_mode == "stream":
                return self._load_alpaca_stream(symbol)
            raise ValueError(f"Unsupported Alpaca data mode: {self.alpaca_data_mode}")
        raise ValueError(f"Unsupported data source: {self.source}")
