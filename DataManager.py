import configparser
import os
import pandas as pd
import ccxt
import mplfinance as mpf

class Fetcher:
    def __init__(self) -> None:
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.exchange_name = config.get('DEFAULT', 'exchange_name', fallback='binance')
        proxy = config.get('DEFAULT', 'proxy', fallback=None)
        timeout = config.getint('DEFAULT', 'timeout', fallback=10000)

        self.exchange = getattr(ccxt, self.exchange_name)()
        self.exchange.httpsProxy = proxy
        self.exchange.timeout = timeout
        self.data = None

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
        self.data = df

    def save(self, filename=None):
        if self.data is None:
            raise ValueError("Data not fetched yet!")
        
        if not filename:
            filename = self.file_name
        
        self.data.to_csv(filename)

    def load(self, filename=None):
        if not filename:
            filename = 'data.csv'
        
        if not os.path.exists(filename):
            raise ValueError(f"File {filename} does not exist!")
        
        self.data = pd.read_csv(filename, index_col='date', parse_dates=True)

    def show(self):
        if self.data is None:
            raise ValueError("Data not available!")
        
        # Plot the candlestick chart
        mpf.plot(self.data, type='candle', volume=True, show_nontrading=True, style='charles')

class Clean:
    def __init__(self) -> None:
        pass

class Aggregator:
    def __init__(self) -> None:
        pass

if __name__ == "__main__":
    fetcher = Fetcher()
    fetcher.fetch('BTC/USDT', '2022-01-01T00:00:00Z', '2022-02-01T00:00:00Z')
    fetcher.show()



    
