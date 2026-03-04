import argparse
from pprint import pprint

from quantlab.config import Settings
from quantlab.db.repository import Repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect current QuantLab SQLite state and recent records.")
    parser.add_argument("--limit", type=int, default=5, help="Number of recent rows to show. Default: 5")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings()
    repository = Repository(db_path=settings.db_path)

    state = repository.load_portfolio_state()
    rebalances = repository.query_recent_rebalances(limit=max(1, args.limit))
    events = repository.query_recent_order_events(limit=max(1, args.limit))
    bars = repository.query_recent_market_bars(limit=max(1, args.limit))

    print("Portfolio State")
    pprint(
        {
            "current_positions": state.current_positions,
            "last_target_weights": state.last_target_weights,
            "last_rebalance_at": state.last_rebalance_at,
            "pending_order_ids": state.pending_order_ids,
        }
    )

    print("\nRecent Rebalances")
    if not rebalances:
        print("(none)")
    else:
        for item in rebalances:
            pprint(item)

    print("\nRecent Order Events")
    if not events:
        print("(none)")
    else:
        for item in events:
            pprint(item)

    print("\nRecent Market Bars")
    if not bars:
        print("(none)")
    else:
        for item in bars:
            pprint(item)


if __name__ == "__main__":
    main()
