from math import floor

from quantlab.types import OrderIntent


class PositionSizer:
    def size_orders(
        self,
        target_weights: dict[str, float],
        latest_prices: dict[str, float],
        equity: float,
        current_positions: dict[str, int] | None = None,
        allow_short: bool = False,
    ) -> list[OrderIntent]:
        current_positions = current_positions or {}
        orders: list[OrderIntent] = []
        for symbol, weight in target_weights.items():
            price = latest_prices.get(symbol)
            if price is None or price <= 0:
                continue

            sign = 1 if weight > 0 else -1 if weight < 0 else 0
            target_notional = abs(weight) * equity
            target_quantity = sign * floor(target_notional / price)
            current_quantity = int(current_positions.get(symbol, 0))

            if not allow_short and target_quantity < 0:
                target_quantity = 0

            delta_quantity = target_quantity - current_quantity
            if delta_quantity == 0:
                continue

            side = "buy" if delta_quantity > 0 else "sell"
            orders.append(
                OrderIntent(
                    symbol=symbol,
                    side=side,
                    quantity=abs(delta_quantity),
                    current_quantity=current_quantity,
                    target_quantity=target_quantity,
                    target_weight=weight,
                    reference_price=price,
                )
            )

        return orders
