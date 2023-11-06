import os
import pandas as pd
import mplfinance as mpf
from Neilyst import Neilyst

class Fetcher(Neilyst):
    def __init__(self, exchange_name):
        super().__init__(exchange_name)

    def fetch(self, symbol, start_date, end_date, timeframe='1d'):
        self.file_name = f'{self.exchange_name}-{start_date}-{end_date}-{timeframe}'
        since = self.exchange.parse8601(start_date)
        end = self.exchange.parse8601(end_date)

        all_candles = []
        while since < end:
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, since)
            if len(candles) == 0:
                break
            since = candles[-1][0] + 1
            all_candles += candles

        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('date', inplace=True, drop=True)
        self.ohlcv_data = df

    def save(self, filename=None):
        if self.ohlcv_data is None:
            raise ValueError("Data not fetched yet!")
        
        if not filename:
            filename = self.file_name
        
        self.ohlcv_data.to_csv(filename)

    def load(self, filename=None):
        if not filename:
            filename = 'data.csv'
        
        if not os.path.exists(filename):
            raise ValueError(f"File {filename} does not exist!")
        
        self.ohlcv_data = pd.read_csv(filename, index_col='date', parse_dates=True)

    def show(self):
        if self.ohlcv_data is None:
            raise ValueError("Data not available!")
        
        # Plot the candlestick chart
        mpf.plot(self.ohlcv_data, type='candle', volume=True, show_nontrading=True, style='charles')

class Clean:
    def __init__(self) -> None:
        pass

class Aggregator:
    def __init__(self) -> None:
        pass

if __name__ == "__main__":
    fetcher = Fetcher('binanceusdm')
    fetcher.fetch('BTC/USDT', '2022-01-01T00:00:00Z', '2022-02-01T00:00:00Z')
    # fetcher.show()
    print(fetcher.ohlcv_data.head())




    
