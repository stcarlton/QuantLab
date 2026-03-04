from quantlab.runtime.engine_loop import run_engine_loop


class FakeEngine:
    def __init__(self, fail_with_keyboard_interrupt: bool = False) -> None:
        self.runs = 0
        self.fail_with_keyboard_interrupt = fail_with_keyboard_interrupt

    def run(self) -> None:
        if self.fail_with_keyboard_interrupt:
            raise KeyboardInterrupt
        self.runs += 1


def test_run_engine_loop_stops_at_max_runs() -> None:
    engine = FakeEngine()

    runs = run_engine_loop(
        engine=engine,  # type: ignore[arg-type]
        interval_seconds=1,
        max_runs=3,
        sleep_fn=lambda _: None,
    )

    assert runs == 3
    assert engine.runs == 3


def test_run_engine_loop_stops_at_timeout() -> None:
    engine = FakeEngine()
    timeline = iter([0.0, 0.0, 1.0, 2.0, 3.1])

    runs = run_engine_loop(
        engine=engine,  # type: ignore[arg-type]
        interval_seconds=1,
        timeout_seconds=3,
        now_fn=lambda: next(timeline),
        sleep_fn=lambda _: None,
    )

    assert runs == 4
    assert engine.runs == 4


def test_run_engine_loop_handles_keyboard_interrupt() -> None:
    engine = FakeEngine(fail_with_keyboard_interrupt=True)

    runs = run_engine_loop(
        engine=engine,  # type: ignore[arg-type]
        interval_seconds=1,
        max_runs=5,
        sleep_fn=lambda _: None,
    )

    assert runs == 0
