import json
from typing import Any
from urllib import parse, request

from quantlab.config import Settings


class UniverseSelector:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _parse_static_symbols(self) -> list[str]:
        if self.settings.symbols_csv:
            symbols = [token.strip().upper() for token in self.settings.symbols_csv.split(",") if token.strip()]
            if symbols:
                return symbols
        return [self.settings.symbol.upper()]

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
            headers={
                "APCA-API-KEY-ID": self.settings.alpaca_key_id or "",
                "APCA-API-SECRET-KEY": self.settings.alpaca_secret_key or "",
            },
            method="GET",
        )
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            payload = json.loads(body)
            if not isinstance(payload, list):
                raise RuntimeError("Unexpected Alpaca assets response format.")
            return payload

    def _select_alpaca_assets(self) -> list[str]:
        assets = self._fetch_alpaca_assets()
        symbols: list[str] = []
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            if not asset.get("tradable", False):
                continue
            symbol = asset.get("symbol")
            if not isinstance(symbol, str):
                continue
            if self.settings.allow_short and not asset.get("shortable", False):
                continue
            symbols.append(symbol.upper())

        symbols = sorted(set(symbols))
        limit = max(1, self.settings.universe_limit)
        return symbols[:limit]

    def select(self) -> list[str]:
        if self.settings.universe_mode == "static":
            return self._parse_static_symbols()
        if self.settings.universe_mode == "alpaca_assets":
            symbols = self._select_alpaca_assets()
            if not symbols:
                raise ValueError("Alpaca assets universe is empty after filters.")
            return symbols
        raise ValueError(f"Unsupported universe mode: {self.settings.universe_mode}")
