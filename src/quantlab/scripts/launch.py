import argparse
from dataclasses import replace

from quantlab.config import Settings
from quantlab.engine import Engine
from quantlab.runtime.engine_loop import run_engine_loop


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch QuantLab with simple mode defaults.")
    parser.add_argument(
        "--mode",
        choices=["test", "live"],
        default="test",
        help="Launch profile. Default: test",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuous loop. Default behavior is loop mode for both profiles.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single cycle only.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=None,
        help="Loop interval override.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=None,
        help="Loop timeout override. 0 means no timeout.",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Enable order submission (off by default, even in live mode).",
    )
    return parser


def profile_settings(base: Settings, mode: str) -> Settings:
    if mode == "test":
        return replace(
            base,
            data_source="synthetic",
            execution_provider="paper_stub",
            submit_orders=False,
            loop_interval_seconds=30,
            loop_timeout_seconds=0,
            run_loop=True,
        )

    return replace(
        base,
        data_source="alpaca",
        alpaca_data_mode="stream",
        alpaca_data_feed="iex",
        execution_provider="alpaca_paper",
        submit_orders=False,
        loop_interval_seconds=30,
        loop_timeout_seconds=0,
        run_loop=True,
    )


def main() -> None:
    args = build_parser().parse_args()
    base = Settings()
    settings = profile_settings(base, args.mode)

    if args.submit:
        settings = replace(settings, submit_orders=True)

    if args.interval_seconds is not None:
        settings = replace(settings, loop_interval_seconds=max(1, args.interval_seconds))
    if args.timeout_seconds is not None:
        settings = replace(settings, loop_timeout_seconds=max(0, args.timeout_seconds))

    if args.once:
        settings = replace(settings, run_loop=False)
    elif args.loop:
        settings = replace(settings, run_loop=True)

    engine = Engine(settings)
    if settings.run_loop:
        runs = run_engine_loop(
            engine=engine,
            interval_seconds=settings.loop_interval_seconds,
            timeout_seconds=settings.loop_timeout_seconds,
        )
        print(f"Run loop completed after {runs} run(s).")
    else:
        engine.run()


if __name__ == "__main__":
    main()
