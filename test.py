import Neilyst

data_1h = Neilyst.get_klines('BTC/USDT', '2023-01-01T00:00:00Z', '2023-12-30T00:00:00Z', timeframe='1h')
data_30m = Neilyst.get_klines('BTC/USDT', '2023-01-01T00:00:00Z', '2023-12-30T00:00:00Z', timeframe='30m')
data_15m = Neilyst.get_klines('BTC/USDT', '2023-01-01T00:00:00Z', '2023-12-30T00:00:00Z', timeframe='15m')
data_5m = Neilyst.get_klines('BTC/USDT', '2023-01-01T00:00:00Z', '2023-12-30T00:00:00Z', timeframe='5m')
data_1m = Neilyst.get_klines('BTC/USDT', '2023-01-01T00:00:00Z', '2023-12-30T00:00:00Z', timeframe='1m')

# 计算指标

indicators_1h = Neilyst.get_indicators(data_1h, 'rsi', 'sma20', 'ema9')
indicators_30m = Neilyst.get_indicators(data_30m, 'rsi', 'sma20', 'ema9')
indicators_15m = Neilyst.get_indicators(data_15m, 'rsi', 'sma20', 'ema9')
indicators_5m= Neilyst.get_indicators(data_5m, 'rsi', 'sma20', 'ema9')
indicators_1m= Neilyst.get_indicators(data_1m, 'rsi', 'sma20', 'ema9')
class MultiSignalStrategy(Neilyst.Strategy):
    def __init__(self, total_balance, trading_fee_ratio, slippage_ratio, data=None, indicators=None):
        super().__init__(total_balance, trading_fee_ratio, slippage_ratio, data, indicators)
        self.take_profit_ratio = 0.2 #止盈比例
        self.stop_loss_ratio = -0.1 #止损比例
    
    def run(self, date, price_row, current_pos, current_balance):
        recent_data_15m = self.get_recent_data(date, 2, data_15m, indicators_15m)
        signal = None
        
        if len(recent_data_15m) >= 2:
            ema_15 = indicators_15m.iloc[0]['ema9']
            ma_15 = indicators_15m.iloc[0]['sma20']

            prev_ema_15 = indicators_15m.iloc[-1]['ema9']
            prev_ma_15 = indicators_15m.iloc[-1]['sma20']

            if current_pos.amount > 0:
                # 此时有仓位，考虑平仓过程
                # 固定止盈止损、或者布林带止盈，ma止损
                open_total_price = current_pos.open_price * current_pos.amount
                if (current_pos.float_profit / open_total_price) >= self.take_profit_ratio:
                    #止盈
                    signal = Neilyst.Signal('close', price_row['close'], current_pos.amount)
                elif (current_pos.float_profit / open_total_price) <= self.stop_loss_ratio:
                    #止损
                    signal = Neilyst.Signal('close', price_row['close'], current_pos.amount)

            else:
                # 没有仓位，考虑开仓信号
                # 加权信号处理
                index = 0
                if (ema_15 > ma_15) and (prev_ema_15 < prev_ma_15):
                    # 多信号
                    index = 1
                if (ema_15 < ma_15) and (prev_ema_15 > prev_ma_15):
                    index = -1

                # 根据信号计算仓位
                pos = abs(current_balance / price_row['close'] * index)

                # 开仓
                if index > 0:
                    signal = Neilyst.Signal('long', price_row['close'], pos)
                elif index < 0:
                    signal = Neilyst.Signal('short', price_row['close'], pos)

        return signal
    
    # 仓位管理，考虑写入框架的策略：网格
    def pos_management(self):
        pass
init_balance = 50000
strategy = MultiSignalStrategy(init_balance, 0, 0, None, None)
result = Neilyst.backtest('BTC/USDT', '2023-01-01T00:00:00Z', '2023-12-30T00:00:00Z', strategy)
evaluation = Neilyst.evaluate_strategy(result, init_balance)
Neilyst.show_pnl(data_15m, indicators_15m, result, init_balance)
