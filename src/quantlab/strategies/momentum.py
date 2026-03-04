from quantlab.strategies.base_strategy import BaseStrategy
from quantlab.types import Bar, Signal


class MomentumStrategy(BaseStrategy):
    strategy_id = "momentum_v1"

    def on_bar(self, bar: Bar) -> Signal | None:
        if bar.close > bar.open:
            direction = "long"
            confidence = min((bar.close - bar.open) / bar.open * 100, 1.0)
        elif bar.close < bar.open:
            direction = "short"
            confidence = min((bar.open - bar.close) / bar.open * 100, 1.0)
        else:
            direction = "flat"
            confidence = 0.0

        return Signal(
            strategy_id=self.strategy_id,
            symbol=bar.symbol,
            direction=direction,
            confidence=confidence,
            timestamp=bar.timestamp,
        )
