import argparse
import time

from quantlab.config import Settings
from quantlab.engine import Engine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reconcile pending Alpaca paper orders from local state.")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously until timeout. Default is single pass.",
    )
    parser.add_argument("--interval-seconds", type=int, default=30, help="Polling interval in seconds. Default: 30")
    parser.add_argument("--timeout-seconds", type=int, default=600, help="Max run time in seconds. Default: 600")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings()
    engine = Engine(settings)

    if not args.loop:
        count = engine.reconcile_orders_once()
        print(f"Reconciled terminal orders: {count}")
        return

    start = time.time()
    total_terminal = 0
    while True:
        count = engine.reconcile_orders_once()
        total_terminal += count
        print(f"Reconciled terminal orders this pass: {count} (total={total_terminal})")

        elapsed = time.time() - start
        if elapsed >= args.timeout_seconds:
            print("Timeout reached.")
            break
        time.sleep(max(1, args.interval_seconds))


if __name__ == "__main__":
    main()
