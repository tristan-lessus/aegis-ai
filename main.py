from feeds.provider_factory import ProviderFactory
from config.settings import DEFAULT_MARKETS, ENTRY_TIMEFRAME


def print_banner():
    print("=" * 50)
    print("                AEGIS AI")
    print("=" * 50)


def main():

    print_banner()

    provider = ProviderFactory.create("live")

    for market in DEFAULT_MARKETS:

        print(f"\nLoading {market}...")

        candles = provider.get_candles(
            symbol=market,
            timeframe=ENTRY_TIMEFRAME,
            count=100
        )

        print(f"Candles received: {len(candles)}")

        last = candles[-1]

        print()

        print("Latest Candle")

        print("-------------------------")

        print(f"Time   : {last.time}")
        print(f"Open   : {last.open}")
        print(f"High   : {last.high}")
        print(f"Low    : {last.low}")
        print(f"Close  : {last.close}")
        print(f"Volume : {last.volume}")


if __name__ == "__main__":
    main()
