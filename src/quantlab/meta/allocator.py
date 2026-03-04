from quantlab.types import Signal


class Allocator:
    def allocate(self, signals: list[Signal]) -> dict[str, float]:
        weights: dict[str, float] = {}
        actionable = [signal for signal in signals if signal.direction != "flat"]
        if not actionable:
            return weights

        per_signal_weight = 1.0 / len(actionable)
        for signal in actionable:
            sign = 1.0 if signal.direction == "long" else -1.0
            weights[signal.symbol] = weights.get(signal.symbol, 0.0) + sign * per_signal_weight * signal.confidence
        return {symbol: round(weight, 6) for symbol, weight in weights.items()}
