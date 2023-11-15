import os
import pandas as pd
import mplfinance as mpf
from BaseNeilyst import BaseNeilyst

class Fetcher(BaseNeilyst):
    def __init__(self, exchange_name):
        super().__init__(exchange_name)

    def fetch(self, symbol, start_date, end_date, timeframe='1h'):
        formatted_symbol = symbol.replace('/', '_')
        self.file_name = f'{self.exchange_name}-{formatted_symbol}-{start_date}-{end_date}-{timeframe}'
        since = self.exchange.parse8601(start_date)
        end = self.exchange.parse8601(end_date)

        all_candles = []
        while since < end:
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, since)
            if len(candles) == 0:
                break
            last_time = candles[-1][0]
            since = last_time + self.exchange.parse_timeframe(timeframe) * 1000
            all_candles += candles
            if last_time >= end:
                break

        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('date', inplace=True, drop=True)

        # 日期过滤
        start_date_time = pd.to_datetime(start_date, utc=True)
        end_date_time = pd.to_datetime(end_date, utc=True)
        df = df[(df.index >= start_date_time) & (df.index < end_date_time)]

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

    def show_ohlcv(self):
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





    
