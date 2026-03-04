import sys
import os

if __name__ == "__main__" and (not __package__):
    # Support direct file execution (`python src/quantlab/main.py`) by ensuring
    # imports resolve from `src` instead of `src/quantlab`, which can shadow stdlib modules.
    package_root = os.path.dirname(os.path.abspath(__file__))
    src_root = os.path.dirname(package_root)
    sys.path = [p for p in sys.path if os.path.abspath(p) != package_root]
    if src_root not in sys.path:
        sys.path.insert(0, src_root)

from dataclasses import replace

from quantlab.config import Settings
from quantlab.engine import Engine
from quantlab.runtime.engine_loop import run_engine_loop


DEBUG_SETTINGS_OVERRIDES: dict[str, object] = {
    # Example:
    # "run_loop": True,
    # "loop_interval_seconds": 30,
    # "loop_timeout_seconds": 0,
    # "execution_provider": "alpaca_paper",
    # "submit_orders": False,
}


def main() -> None:
    settings = Settings()
    if DEBUG_SETTINGS_OVERRIDES:
        settings = replace(settings, **DEBUG_SETTINGS_OVERRIDES)
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
