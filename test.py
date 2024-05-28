import Neilyst

start_time = '2024-03-23T00:00:00Z'
end_time = '2024-04-08T00:00:00Z'
symbol = 'SOL/USDT'

data = Neilyst.get_klines(symbol, start_time, end_time, timeframe='15m')
indicators = Neilyst.get_indicators(data, 'sma20')


class MultiSignalStrategy(Neilyst.Strategy):
    def __init__(self, total_balance, trading_fee_ratio, slippage_ratio, data=None, indicators=None):
        super().__init__(total_balance, trading_fee_ratio, slippage_ratio, data, indicators)
        self.take_profit_ratio = 0.2 #止盈比例
        self.stop_loss_ratio = -0.1 #止损比例
    def run(self, date, price_row, current_pos, current_balance):
        recent_data = self.get_recent_data(date, 1, data, indicators)

        index = 0
        price = price_row['close']
        signal_num = ((price * 10) % 10).astype(int)
        ma = recent_data.iloc[-1]['sma20']
        signal = None

        # print(price, ma, signal_num)
        if price > ma and signal_num == 1:
            index = 1
        
        if price < ma and signal_num == 9:
            index = -1

        if current_pos.amount > 0:
            # 此时有仓位，考虑平仓过程
            # 固定止盈止损、或者布林带止盈，ma止损

            # 查看信号是否消失
            if current_pos.amount > 0 and index == -1:
                signal = Neilyst.Signal('close', price_row['close'], current_pos.amount)
            elif current_pos.amount < 0 and index == 1:
                #止损
                signal = Neilyst.Signal('close', price_row['close'], current_pos.amount)

        else:

            # 根据信号计算仓位
            pos = abs(current_balance / price_row['close'])

            # 开仓
            if index > 0:
                signal = Neilyst.Signal('long', price_row['close'], pos)
            elif index < 0:
                signal = Neilyst.Signal('short', price_row['close'], pos)

        # print(signal)
        return signal
    
init_balance = 200
strategy = MultiSignalStrategy(init_balance, 0.0002, 0.001, None, None)
result = Neilyst.backtest(symbol, start_time, end_time, strategy)
evaluation = Neilyst.evaluate_strategy(result, init_balance)
# Neilyst.show_pnl(data, indicators, result, init_balance)