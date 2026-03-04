"""Data storage interfaces."""

from quantlab.types import Bar


class DataStorage:
    def persist_bars(self, bars: list[Bar]) -> None:
        return None
