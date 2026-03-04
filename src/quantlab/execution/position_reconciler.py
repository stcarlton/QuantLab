from math import trunc


def positions_from_broker(raw_positions: list[dict[str, object]]) -> dict[str, int]:
    positions: dict[str, int] = {}
    for item in raw_positions:
        symbol_obj = item.get("symbol")
        qty_obj = item.get("qty")
        if not isinstance(symbol_obj, str):
            continue
        if qty_obj is None:
            continue

        try:
            qty = trunc(float(str(qty_obj)))
        except ValueError:
            continue
        positions[symbol_obj] = qty
    return positions
