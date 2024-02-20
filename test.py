import Neilyst

data = Neilyst.get_klines('BTC/USDT', '2023-01-01T00:00:00Z', '2023-01-30T00:00:00Z', timeframe='1h')
indicators = Neilyst.get_indicators(data, 'rsi', 'sma20', 'sma60', 'sma120')
class MovingAverageStrategy(Neilyst.Strategy):
    def __init__(self, total_balance, trading_fee_ratio, slippage_ratio, data, indicators):
        super().__init__(total_balance, trading_fee_ratio, slippage_ratio, data, indicators)
        self.short_window = 20
        self.long_window = 60

    def run(self, date, price_row, current_pos, current_balance):
        recent_data = self.get_recent_data(date, 2)
        print(recent_data)
        # if len(recent_data) >= 2:
        #     short_mavg = recent_data['sma20'].head(1)
        #     long_mavg = recent_data['sma60'].head(1)

        #     prev_short_mavg = recent_data['sma20'].tail(1)
        #     prev_long_mavg = recent_data['sma60'].tail(1)

        #     if short_mavg > long_mavg and (prev_short_mavg < prev_long_mavg):
        #         signal = Neilyst.Signal('long', price_row['close'], 1)
        #     elif short_mavg < long_mavg and (prev_short_mavg > prev_long_mavg):
        #         if current_pos.amount > 0:
        #             signal = Neilyst.Signal('close', price_row['close'], current_pos.amount)
        #         else:
        #             signal = None
        #     else:
        #         signal = None
        # else:
        #     signal = None
        
        # return signal

strategy = MovingAverageStrategy(50000, 0, 0, data, indicators)
result = Neilyst.backtest('BTC/USDT', '2023-01-01T00:00:00Z', '2023-01-03T00:00:00Z', strategy)