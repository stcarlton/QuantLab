import argparse

from quantlab.config import Settings
from quantlab.execution.alpaca_broker import AlpacaBroker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Alpaca paper order status by order id.")
    parser.add_argument("--order-id", required=True, help="Alpaca order id to inspect")
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

    order = broker.get_order(args.order_id)
    print(f"Order ID: {order.get('id')}")
    print(f"Status: {order.get('status')}")
    print(f"Symbol: {order.get('symbol')}")
    print(f"Side: {order.get('side')}")
    print(f"Qty: {order.get('qty')}")
    print(f"Filled Qty: {order.get('filled_qty')}")
    print(f"Submitted At: {order.get('submitted_at')}")
    print(f"Filled At: {order.get('filled_at')}")


if __name__ == "__main__":
    main()
