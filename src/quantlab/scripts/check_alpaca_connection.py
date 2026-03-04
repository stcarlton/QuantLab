from quantlab.config import Settings
from quantlab.execution.alpaca_broker import AlpacaBroker


def main() -> None:
    settings = Settings()
    settings.require_alpaca_credentials()

    broker = AlpacaBroker(
        key_id=settings.alpaca_key_id or "",
        secret_key=settings.alpaca_secret_key or "",
        base_url=settings.alpaca_base_url,
    )
    account = broker.get_account()

    print("Connected to Alpaca paper API.")
    print(f"Account ID: {account.get('id')}")
    print(f"Status: {account.get('status')}")
    print(f"Cash: {account.get('cash')}")
    print(f"Buying Power: {account.get('buying_power')}")


if __name__ == "__main__":
    main()
