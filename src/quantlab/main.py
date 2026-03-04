from quantlab.config import Settings
from quantlab.engine import Engine
from quantlab.runtime.engine_loop import run_engine_loop


def main() -> None:
    settings = Settings()
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
