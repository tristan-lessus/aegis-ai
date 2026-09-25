from feeds.csv_provider import CSVProvider
from feeds.live_provider import LiveProvider
from config.settings import API_KEY


class ProviderFactory:

    @staticmethod
    def create(provider="live"):

        if provider.lower() == "live":
            return LiveProvider(API_KEY)

        elif provider.lower() == "csv":
            return CSVProvider()

        raise ValueError(f"Unknown provider: {provider}")
