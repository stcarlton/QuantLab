import argparse
import time

from quantlab.config import Settings
from quantlab.execution.alpaca_broker import AlpacaBroker


TERMINAL_STATES = {"filled", "canceled", "rejected", "expired"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Poll Alpaca order status until terminal state or timeout.")
    parser.add_argument("--order-id", required=True, help="Alpaca order id to monitor")
    parser.add_argument("--interval-seconds", type=int, default=5, help="Polling interval in seconds. Default: 5")
    parser.add_argument("--timeout-seconds", type=int, default=300, help="Max wait in seconds. Default: 300")
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

    start = time.time()
    last_status = None
    while True:
        order = broker.get_order(args.order_id)
        status = str(order.get("status", "")).lower()

        if status != last_status:
            print(
                f"Status={status} filled_qty={order.get('filled_qty')} "
                f"filled_at={order.get('filled_at')} updated_at={order.get('updated_at')}"
            )
            last_status = status

        if status in TERMINAL_STATES:
            print("Reached terminal state.")
            break

        elapsed = time.time() - start
        if elapsed >= args.timeout_seconds:
            print("Timeout reached before terminal state.")
            break

        time.sleep(max(1, args.interval_seconds))


if __name__ == "__main__":
    main()
