from DataManager import Fetcher
import pandas as pd
import mplfinance as mpf

class Indicators(Fetcher):
    def __init__(self, exchange_name) -> None:
        super().__init__(exchange_name)

    def __set_index(self) -> None:
        self.indicators = pd.DataFrame(index=self.ohlcv_data.index)

    def MA(self, l) -> None:
        """
        Calculate the Moving Average for the given length 'l'.

        l: Length of the window for the moving average.

        """

        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")
        
        if self.indicators is None:
            self.__set_index()
        
        ma_series = self.ohlcv_data['close'].rolling(window=l).mean()
        # Forward fill the NaN values
        ma_series_filled = ma_series.fillna(method='bfill')
    
        self.indicators[f'MA{l}'] = ma_series_filled

    def EMA(self, l) -> None:
        """
        Calculate the Exponential Moving Average for the given length 'l'.

        l: Length of the window for the exponential moving average.
        """
        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")
        
        if self.indicators is None:
            self.__set_index()

        self.indicators[f'EMA{l}'] = self.ohlcv_data['close'].ewm(span=l, adjust=False).mean()

    def show(self, *args, show_candles=True) -> None:
        """
        Visualize the OHLCV data with the selected indicators.

        Parameters:
        *args : str
            Indicator names to be plotted.
        show_candles : bool, optional
            Whether to show the candlestick chart or not (default is True).
        """
        apds = []  # mplfinance的额外图表样式（指标）

        if show_candles:
            plot_type = 'candle'
        else:
            plot_type = 'line'

        for arg in args:
            if arg in self.indicators:
                # 假设指标已经是一个序列，可以直接绘制。
                # mplfinance要求指标是两个序列的元组：(系列, 配置字典)
                # 如果你的指标需要特别的配置，请在这里添加
                apds.append(mpf.make_addplot(self.indicators[arg]))

        # 如果没有提供任何指标名，则默认展示所有指标
        if not args:
            for indicator_name in self.indicators.columns:
                apds.append(mpf.make_addplot(self.indicators[indicator_name]))

        # 绘制OHLCV数据和指标
        mpf.plot(self.ohlcv_data, type=plot_type, addplot=apds, volume=True, show_nontrading=True, style='charles')


    def show_all(self) -> None:
        """
        Visualize the OHLCV data with all available indicators.
        """
        # 调用show方法，没有提供指标名，函数会显示所有指标
        self.show()

if __name__ == "__main__":
    # 初始化Indicators对象
    indicators = Indicators('binanceusdm')
    # 获取数据
    indicators.fetch('BTC/USDT', '2022-01-01T00:00:00Z', '2022-02-01T00:00:00Z')
    # 计算移动平均线和指数移动平均线
    indicators.MA(5)  # 计算5天移动平均线
    indicators.EMA(50)  # 计算50天指数移动平均线

    print(indicators.indicators.head(10))
    # 测试show方法，只显示MA和蜡烛图
    indicators.show('MA5', 'EMA50')

    # # 测试show_all方法，显示所有指标和蜡烛图
    # indicators.show_all()
