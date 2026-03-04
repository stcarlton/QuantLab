from quantlab.config import Settings
from quantlab.engine import Engine


def test_engine_run_once_with_csv_data_source(tmp_path) -> None:
    csv_path = tmp_path / "bars.csv"
    csv_path.write_text(
        "\n".join(
            [
                "timestamp,symbol,open,high,low,close,volume",
                "2026-03-03T14:30:00+00:00,AAPL,100,101,99,100.8,100000",
                "2026-03-03T14:31:00+00:00,AAPL,100.8,101.3,100.5,101.1,120000",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(
        symbol="AAPL",
        data_source="csv",
        data_csv_path=str(csv_path),
        execution_provider="paper_stub",
        submit_orders=False,
        db_path=str(tmp_path / "quantlab_csv.db"),
    )

    result = Engine(settings).run_once()

    assert result.signal_count == 2
    assert "AAPL" in result.target_weights
    assert len(result.planned_orders) == 1
