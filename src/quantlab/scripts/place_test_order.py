import argparse

from quantlab.config import Settings
from quantlab.execution.alpaca_broker import AlpacaBroker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Place a small Alpaca paper order and print account state.")
    parser.add_argument("--symbol", default="AAPL", help="Ticker symbol. Default: AAPL")
    parser.add_argument("--qty", type=float, default=1.0, help="Order quantity. Default: 1")
    parser.add_argument("--side", choices=["buy", "sell"], default="buy", help="Order side. Default: buy")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm placement. Without this flag, script exits without submitting.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(f"Ready to place paper order: {args.side.upper()} {args.qty} {args.symbol.upper()}")
    if not args.yes:
        print("Dry run only. Re-run with --yes to submit.")
        return

    settings = Settings()
    settings.require_alpaca_credentials()
    broker = AlpacaBroker(
        key_id=settings.alpaca_key_id or "",
        secret_key=settings.alpaca_secret_key or "",
        base_url=settings.alpaca_base_url,
    )

    order = broker.submit_order(symbol=args.symbol.upper(), quantity=args.qty, side=args.side)
    print(f"Submitted order id: {order.get('id')}")
    print(f"Order status: {order.get('status')}")

    open_orders = broker.list_open_orders()
    positions = broker.list_positions()
    print(f"Open orders: {len(open_orders)}")
    print(f"Open positions: {len(positions)}")


if __name__ == "__main__":
    main()
