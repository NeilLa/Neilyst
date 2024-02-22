import Neilyst

data = Neilyst.get_klines('BTC/USDT', '2023-01-01T00:00:00Z', '2023-01-03T00:00:00Z', timeframe='1h')

indicators = Neilyst.get_indicators(data, 'rsi', 'sma5', 'sma10')
class MovingAverageStrategy(Neilyst.Strategy):
    def __init__(self, total_balance, trading_fee_ratio, slippage_ratio, data, indicators):
        super().__init__(total_balance, trading_fee_ratio, slippage_ratio, data, indicators)
        self.short_window = 20
        self.long_window = 60

    def run(self, date, price_row, current_pos, current_balance):
        recent_data = self.get_recent_data(date, 2)
        if len(recent_data) >= 2:
            short_mavg = recent_data.iloc[0]['sma5']
            long_mavg = recent_data.iloc[0]['sma10']

            prev_short_mavg = recent_data.iloc[-1]['sma5']
            prev_long_mavg = recent_data.iloc[-1]['sma10']

            if short_mavg > long_mavg and (prev_short_mavg < prev_long_mavg):
                if current_pos.amount == 0:
                    print('open, ' + str(date))
                    signal = Neilyst.Signal('long', price_row['close'], 1)
                else:
                    signal = None
            elif short_mavg < long_mavg and (prev_short_mavg > prev_long_mavg):
                if current_pos.amount > 0:
                    print('close, ' + str(date))
                    signal = Neilyst.Signal('close', price_row['close'], current_pos.amount)
                else:
                    signal = None
            else:
                signal = None
        else:
            signal = None
        
        return signal

strategy = MovingAverageStrategy(50000, 0, 0, data, indicators)
result = Neilyst.backtest('BTC/USDT', '2023-01-01T00:00:00Z', '2023-01-02T00:00:00Z', strategy)
print(result)