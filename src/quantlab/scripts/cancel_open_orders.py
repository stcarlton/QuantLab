import argparse

from quantlab.config import Settings
from quantlab.execution.alpaca_broker import AlpacaBroker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely cancel open Alpaca paper orders.")
    parser.add_argument("--symbol", default=None, help="Optional symbol filter (e.g. AAPL)")
    parser.add_argument(
        "--max-orders",
        type=int,
        default=5,
        help="Maximum orders to cancel in one run. Default: 5",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm cancellation. Without this flag, script runs in dry-run mode.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings()
    settings.require_alpaca_credentials()

    broker = AlpacaBroker(
        key_id=settings.alpaca_key_id or "",
        secret_key=settings.alpaca_secret_key or "",
        base_url=settings.alpaca_base_url,
    )

    open_orders = broker.list_open_orders()
    if args.symbol:
        symbol_filter = args.symbol.upper()
        open_orders = [o for o in open_orders if str(o.get("symbol", "")).upper() == symbol_filter]

    if args.max_orders > 0:
        open_orders = open_orders[: args.max_orders]

    print(f"Matched open orders: {len(open_orders)}")
    for order in open_orders:
        print(f"- id={order.get('id')} symbol={order.get('symbol')} side={order.get('side')} qty={order.get('qty')}")

    if not args.yes:
        print("Dry run only. Re-run with --yes to cancel.")
        return

    canceled = 0
    for order in open_orders:
        order_id = order.get("id")
        if not isinstance(order_id, str):
            continue
        broker.cancel_order(order_id)
        canceled += 1

    print(f"Canceled orders: {canceled}")


if __name__ == "__main__":
    main()
