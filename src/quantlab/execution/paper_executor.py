from typing import Any, Literal

from quantlab.execution.broker_interface import BrokerInterface


class PaperExecutor(BrokerInterface):
    def submit_order(
        self,
        symbol: str,
        quantity: float,
        side: Literal["buy", "sell"] = "buy",
        order_type: Literal["market"] = "market",
        time_in_force: Literal["day", "gtc"] = "day",
    ) -> dict[str, Any]:
        return {
            "id": "paper-order",
            "symbol": symbol,
            "qty": quantity,
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
            "status": "accepted",
        }

    def get_account(self) -> dict[str, Any]:
        return {
            "id": "paper-account",
            "status": "ACTIVE",
            "cash": "100000",
            "buying_power": "100000",
        }

    def get_order(self, order_id: str) -> dict[str, Any]:
        return {
            "id": order_id,
            "status": "unknown",
        }

    def list_open_orders(self) -> list[dict[str, Any]]:
        return []

    def list_positions(self) -> list[dict[str, Any]]:
        return []

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        return {"id": order_id, "status": "canceled"}

    def cancel_all_open_orders(self) -> list[dict[str, Any]]:
        return []
