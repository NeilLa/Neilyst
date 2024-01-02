import Neilyst

data = Neilyst.get_klines('BTC/USDT', '2023-01-10T00:00:00Z', '2023-01-14T00:00:00Z', timeframe='1h')
print(data)