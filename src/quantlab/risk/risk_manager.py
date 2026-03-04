from quantlab.types import BlockedOrderIntent, OrderIntent


class RiskManager:
    def __init__(
        self,
        max_position_weight: float,
        max_gross_exposure: float,
        max_order_notional: float,
        daily_loss_limit_pct: float,
        kill_switch: bool,
    ) -> None:
        self.max_position_weight = max_position_weight
        self.max_gross_exposure = max_gross_exposure
        self.max_order_notional = max_order_notional
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.kill_switch = kill_switch

    def validate_target_weights(self, weights: dict[str, float]) -> dict[str, float]:
        constrained = {
            symbol: max(-self.max_position_weight, min(self.max_position_weight, weight))
            for symbol, weight in weights.items()
        }

        gross = sum(abs(weight) for weight in constrained.values())
        if gross > self.max_gross_exposure and gross > 0:
            scale = self.max_gross_exposure / gross
            constrained = {symbol: weight * scale for symbol, weight in constrained.items()}
        return constrained

    def filter_order_intents(
        self,
        intents: list[OrderIntent],
        equity_used: float,
        starting_cash: float,
    ) -> tuple[list[OrderIntent], list[BlockedOrderIntent], bool, bool]:
        blocked: list[BlockedOrderIntent] = []
        if self.kill_switch:
            return [], [BlockedOrderIntent(intent=i, reason="kill_switch") for i in intents], True, False

        daily_loss_hit = False
        if starting_cash > 0:
            daily_loss_pct = max(0.0, (starting_cash - equity_used) / starting_cash)
            if daily_loss_pct >= self.daily_loss_limit_pct:
                daily_loss_hit = True
                return [], [BlockedOrderIntent(intent=i, reason="daily_loss_limit") for i in intents], False, True

        approved: list[OrderIntent] = []
        for intent in intents:
            notional = intent.quantity * intent.reference_price
            if notional > self.max_order_notional:
                blocked.append(BlockedOrderIntent(intent=intent, reason="max_order_notional"))
                continue
            approved.append(intent)

        return approved, blocked, False, daily_loss_hit
