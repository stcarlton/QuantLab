import json
from typing import Any
from urllib import parse, request

from quantlab.config import Settings


class UniverseSelector:
    _SUPPORTED_EXCHANGES = {"NYSE", "NASDAQ", "ARCA", "AMEX", "BATS"}
    _SNAPSHOT_CHUNK_SIZE = 200

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._cached_alpaca_universe: list[str] | None = None

    def _parse_static_symbols(self) -> list[str]:
        if self.settings.symbols_csv:
            symbols = [token.strip().upper() for token in self.settings.symbols_csv.split(",") if token.strip()]
            if symbols:
                return symbols
        return [self.settings.symbol.upper()]

    def _auth_headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.settings.alpaca_key_id or "",
            "APCA-API-SECRET-KEY": self.settings.alpaca_secret_key or "",
        }

    def _fetch_alpaca_assets(self) -> list[dict[str, Any]]:
        self.settings.require_alpaca_credentials()
        params = parse.urlencode(
            {
                "status": "active",
                "asset_class": "us_equity",
            }
        )
        req = request.Request(
            url=f"{self.settings.alpaca_base_url.rstrip('/')}/v2/assets?{params}",
            headers=self._auth_headers(),
            method="GET",
        )
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            payload = json.loads(body)
            if not isinstance(payload, list):
                raise RuntimeError("Unexpected Alpaca assets response format.")
            return payload

    def _fetch_alpaca_most_actives(self, top: int) -> list[str]:
        self.settings.require_alpaca_credentials()
        requested_top = max(1, min(top, 200))
        params = parse.urlencode({"top": str(requested_top)})
        req = request.Request(
            url=f"{self.settings.alpaca_data_base_url.rstrip('/')}/v1beta1/screener/stocks/most-actives?{params}",
            headers=self._auth_headers(),
            method="GET",
        )
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise RuntimeError("Unexpected Alpaca most-actives response format.")
            rows = payload.get("most_actives", [])
            if not isinstance(rows, list):
                raise RuntimeError("Unexpected Alpaca most-actives payload.")
            symbols: list[str] = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                symbol = row.get("symbol")
                if isinstance(symbol, str) and symbol.strip():
                    symbols.append(symbol.strip().upper())
            return symbols

    def _is_symbol_candidate(self, asset: dict[str, Any]) -> bool:
        if not asset.get("tradable", False):
            return False
        if self.settings.allow_short and not asset.get("shortable", False):
            return False

        exchange = asset.get("exchange")
        if not isinstance(exchange, str) or exchange.upper() not in self._SUPPORTED_EXCHANGES:
            return False

        symbol = asset.get("symbol")
        if not isinstance(symbol, str):
            return False
        normalized = symbol.upper()
        if not normalized.isalpha():
            return False
        if len(normalized) > 5:
            return False
        return True

    def _fetch_snapshots_for_symbols(self, symbols: list[str]) -> dict[str, Any]:
        if not symbols:
            return {}
        params = parse.urlencode(
            {
                "symbols": ",".join(symbols),
                "feed": self.settings.alpaca_data_feed,
            }
        )
        req = request.Request(
            url=f"{self.settings.alpaca_data_base_url.rstrip('/')}/v2/stocks/snapshots?{params}",
            headers=self._auth_headers(),
            method="GET",
        )
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise RuntimeError("Unexpected Alpaca snapshots response format.")
            snapshots = payload.get("snapshots", {})
            if not isinstance(snapshots, dict):
                raise RuntimeError("Unexpected Alpaca snapshots payload.")
            return snapshots

    def _snapshot_dollar_volume(self, snapshot: dict[str, Any]) -> float:
        bar = snapshot.get("dailyBar")
        if not isinstance(bar, dict):
            bar = snapshot.get("prevDailyBar")
            if not isinstance(bar, dict):
                return 0.0
        close = bar.get("c")
        volume = bar.get("v")
        if not isinstance(close, (int, float)) or not isinstance(volume, (int, float)):
            return 0.0
        return float(close) * float(volume)

    def _select_alpaca_assets(self) -> list[str]:
        if self._cached_alpaca_universe is not None:
            return self._cached_alpaca_universe

        limit = max(1, self.settings.universe_limit)
        # Preferred path: use Alpaca's most-actives screener (already liquidity-ranked).
        try:
            most_actives = self._fetch_alpaca_most_actives(top=max(limit * 3, 50))
            selected = []
            for symbol in most_actives:
                if not symbol.isalpha():
                    continue
                if len(symbol) > 5:
                    continue
                selected.append(symbol)
                if len(selected) >= limit:
                    break
            if selected:
                self._cached_alpaca_universe = selected
                return selected
        except Exception:
            # Fallback path below uses assets + snapshots ranking.
            pass

        assets = self._fetch_alpaca_assets()
        candidate_symbols: list[str] = []
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            if not self._is_symbol_candidate(asset):
                continue
            symbol = str(asset["symbol"]).upper()
            candidate_symbols.append(symbol)

        candidate_symbols = sorted(set(candidate_symbols))
        scored: list[tuple[str, float]] = []
        for i in range(0, len(candidate_symbols), self._SNAPSHOT_CHUNK_SIZE):
            batch = candidate_symbols[i : i + self._SNAPSHOT_CHUNK_SIZE]
            snapshots = self._fetch_snapshots_for_symbols(batch)
            for symbol in batch:
                snapshot = snapshots.get(symbol)
                if not isinstance(snapshot, dict):
                    continue
                dollar_volume = self._snapshot_dollar_volume(snapshot)
                if dollar_volume <= 0:
                    continue
                scored.append((symbol, dollar_volume))

        scored.sort(key=lambda item: (-item[1], item[0]))
        selected = [symbol for symbol, _ in scored[:limit]]
        self._cached_alpaca_universe = selected
        return selected

    def select(self) -> list[str]:
        if self.settings.universe_mode == "static":
            return self._parse_static_symbols()
        if self.settings.universe_mode == "alpaca_assets":
            symbols = self._select_alpaca_assets()
            if not symbols:
                raise ValueError("Alpaca assets universe is empty after filters.")
            return symbols
        raise ValueError(f"Unsupported universe mode: {self.settings.universe_mode}")
