import Neilyst
import pandas as pd
# data = Neilyst.get_klines('BTC/USDT', '2023-01-10T00:00:00Z', '2023-01-14T00:00:00Z', timeframe='1h')
# print(data)

history_path = './account.csv'
history = Neilyst.load_history(history_path)
history = Neilyst._filter_close_order(history)

history.to_csv('test.csv')