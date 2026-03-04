from quantlab.data.loader import DataLoader


def test_data_loader_csv_filters_symbol_and_parses_rows(tmp_path) -> None:
    csv_path = tmp_path / "bars.csv"
    csv_path.write_text(
        "\n".join(
            [
                "timestamp,symbol,open,high,low,close,volume",
                "2026-01-01T00:00:00+00:00,AAPL,100,101,99,100.8,100000",
                "2026-01-01T00:00:00+00:00,MSFT,200,201,199,200.2,90000",
            ]
        ),
        encoding="utf-8",
    )

    loader = DataLoader(source="csv", csv_path=str(csv_path))
    bars = loader.load_bars("AAPL")

    assert len(bars) == 1
    assert bars[0].symbol == "AAPL"
    assert bars[0].open == 100.0
    assert bars[0].close == 100.8


def test_data_loader_csv_raises_when_path_missing() -> None:
    loader = DataLoader(source="csv", csv_path="does_not_exist.csv")
    try:
        loader.load_bars("AAPL")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        assert True
