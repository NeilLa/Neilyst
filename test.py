import Neilyst
import pandas as pd
# data = Neilyst.get_klines('BTC/USDT', '2023-01-10T00:00:00Z', '2023-01-14T00:00:00Z', timeframe='1h')
# print(data)

# history_path = './account.csv'
# history = Neilyst.load_history(history_path)
# periods_example = [('2024-01-01', '2024-01-02'), ('2024-01-03', '2024-01-04')]
# symbol_example = 'GMT-USDT-SWAP'
# data = history
# win_rate_all = Neilyst.calculate_win_rate(data)
# win_rate_periods = Neilyst.calculate_win_rate(data, periods=periods_example)
# win_rate_symbol = Neilyst.calculate_win_rate(data, symbol=symbol_example)
# win_rate_periods_symbol = Neilyst.calculate_win_rate(data, periods=periods_example, symbol=symbol_example)

# print(win_rate_symbol)

test = Neilyst.backtest('BTC/USDT', '2023-01-10T00:00:00Z', '2023-01-14T00:00:00Z', 'aaa')