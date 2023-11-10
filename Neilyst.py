from .Strategy import Strategy

class Neilyst(Strategy):
    def __init__(self, exchange_name) -> None:
        super().__init__(exchange_name)