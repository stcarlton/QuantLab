from abc import ABC, abstractmethod

from quantlab.types import Bar, Signal


class BaseStrategy(ABC):
    strategy_id: str

    @abstractmethod
    def on_bar(self, bar: Bar) -> Signal | None:
        raise NotImplementedError
