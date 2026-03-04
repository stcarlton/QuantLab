from abc import ABC, abstractmethod
from typing import Any, Literal


class BrokerInterface(ABC):
    @abstractmethod
    def submit_order(
        self,
        symbol: str,
        quantity: float,
        side: Literal["buy", "sell"] = "buy",
        order_type: Literal["market"] = "market",
        time_in_force: Literal["day", "gtc"] = "day",
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_account(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_order(self, order_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_open_orders(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_positions(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def cancel_all_open_orders(self) -> list[dict[str, Any]]:
        raise NotImplementedError
