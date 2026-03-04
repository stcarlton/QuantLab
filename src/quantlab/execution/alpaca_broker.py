import json
from typing import Any, Literal
from urllib import error, request

from quantlab.execution.broker_interface import BrokerInterface


class AlpacaBroker(BrokerInterface):
    def __init__(self, key_id: str, secret_key: str, base_url: str = "https://paper-api.alpaca.markets") -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret_key,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(
            url=f"{self.base_url}{path}",
            data=data,
            headers=self.headers,
            method=method,
        )

        try:
            with request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8")
                if not body:
                    return {}
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    return {"raw": body}
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            raise RuntimeError(f"Alpaca API request failed ({exc.code}): {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Alpaca API connection failed: {exc.reason}") from exc

    def submit_order(
        self,
        symbol: str,
        quantity: float,
        side: Literal["buy", "sell"] = "buy",
        order_type: Literal["market"] = "market",
        time_in_force: Literal["day", "gtc"] = "day",
    ) -> dict[str, Any]:
        payload = {
            "symbol": symbol,
            "qty": str(quantity),
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
        }
        return self._request("POST", "/v2/orders", payload)

    def get_account(self) -> dict[str, Any]:
        response = self._request("GET", "/v2/account")
        if not isinstance(response, dict):
            raise RuntimeError("Unexpected account response from Alpaca API.")
        return response

    def get_order(self, order_id: str) -> dict[str, Any]:
        response = self._request("GET", f"/v2/orders/{order_id}")
        if not isinstance(response, dict):
            raise RuntimeError("Unexpected order response from Alpaca API.")
        return response

    def list_open_orders(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/v2/orders?status=open")
        if not isinstance(response, list):
            raise RuntimeError("Unexpected open orders response from Alpaca API.")
        return response

    def list_positions(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/v2/positions")
        if not isinstance(response, list):
            raise RuntimeError("Unexpected positions response from Alpaca API.")
        return response

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        response = self._request("DELETE", f"/v2/orders/{order_id}")
        if not isinstance(response, dict):
            raise RuntimeError("Unexpected cancel order response from Alpaca API.")
        return response

    def cancel_all_open_orders(self) -> list[dict[str, Any]]:
        response = self._request("DELETE", "/v2/orders")
        if not isinstance(response, list):
            raise RuntimeError("Unexpected cancel-all response from Alpaca API.")
        return response
