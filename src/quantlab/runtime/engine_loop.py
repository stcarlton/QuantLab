import time
from typing import Protocol

from quantlab.engine import Engine


class Clock(Protocol):
    def __call__(self) -> float: ...


class Sleeper(Protocol):
    def __call__(self, seconds: float) -> None: ...


def run_engine_loop(
    engine: Engine,
    interval_seconds: int = 60,
    timeout_seconds: int = 0,
    max_runs: int = 0,
    now_fn: Clock = time.time,
    sleep_fn: Sleeper = time.sleep,
) -> int:
    start = now_fn()
    runs = 0
    try:
        while True:
            engine.run()
            runs += 1

            if max_runs > 0 and runs >= max_runs:
                break
            if timeout_seconds > 0 and (now_fn() - start) >= timeout_seconds:
                break

            sleep_fn(max(1, interval_seconds))
    except KeyboardInterrupt:
        print("Run loop interrupted by user.")
    return runs
