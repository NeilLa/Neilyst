from Analytics import Indicators

class Strategy(Indicators):
    def __init__(self, exchange_name) -> None:
        super().__init__(exchange_name)

    def long(self) -> None:
        pass

    def short(self) -> None:
        pass

    def close(self) -> None:
        pass

    def take_profit(self) -> None:
        pass

    def stop_loss(self) -> None:
        pass

    