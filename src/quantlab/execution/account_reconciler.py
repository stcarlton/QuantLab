def equity_from_account(account: dict[str, object], fallback_equity: float) -> float:
    for key in ("equity", "portfolio_value", "buying_power"):
        raw = account.get(key)
        if raw is None:
            continue
        try:
            value = float(str(raw))
        except ValueError:
            continue
        if value > 0:
            return value
    return fallback_equity
