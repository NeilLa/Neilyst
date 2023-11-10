from .DataManager import Fetcher
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
    
    def ATR(self, period=14) -> None:
        """
        Calculate the Average True Range (ATR) for the given period.

        period: The number of periods to calculate the ATR over.
        """
        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")
        
        if self.indicators is None:
            self.__set_index()

        high = self.ohlcv_data['high']
        low = self.ohlcv_data['low']
        close = self.ohlcv_data['close']

        # 计算真实范围
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)

        # 计算ATR
        atr = tr.rolling(window=period).mean()
        atr = atr.fillna(method='bfill')
        # 将ATR添加到指标数据中
        self.indicators[f'ATR{period}'] = atr
    
    def SuperTrend(self, period=7, multiplier=3) -> None:
        """
        Calculate the Super Trend indicator.

        period: The period for calculating ATR.
        multiplier: The multiplier for ATR to calculate basic upper and lower bands.
        """
        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")
        
        if self.indicators is None:
            self.__set_index()

        # 计算ATR
        self.ATR(period)
        atr = self.indicators[f'ATR{period}']

        # 基本上下轨
        high = self.ohlcv_data['high']
        low = self.ohlcv_data['low']

        basic_upperband = ((high + low) / 2) + (multiplier * atr)
        basic_lowerband = ((high + low) / 2) - (multiplier * atr)

        # 最终上下轨
        final_upperband = basic_upperband.copy()
        final_lowerband = basic_lowerband.copy()

        for i in range(1, len(final_upperband)):
            # 更新最终上轨
            if basic_upperband[i] < final_upperband[i - 1] or self.ohlcv_data['close'][i - 1] > final_upperband[i - 1]:
                final_upperband[i] = basic_upperband[i]
            else:
                final_upperband[i] = final_upperband[i - 1]

            # 更新最终下轨
            if basic_lowerband[i] > final_lowerband[i - 1] or self.ohlcv_data['close'][i - 1] < final_lowerband[i - 1]:
                final_lowerband[i] = basic_lowerband[i]
            else:
                final_lowerband[i] = final_lowerband[i - 1]

        # 超级趋势
        supertrend = pd.Series(index=self.ohlcv_data.index)
        for i in range(len(supertrend)):
            if i == 0:
                supertrend[i] = final_lowerband[i]
            else:
                if self.ohlcv_data['close'][i] > final_upperband[i - 1]:
                    supertrend[i] = final_lowerband[i]
                elif self.ohlcv_data['close'][i] < final_lowerband[i - 1]:
                    supertrend[i] = final_upperband[i]
                else:
                    supertrend[i] = supertrend[i - 1]

        self.indicators['SuperTrend'] = supertrend


    def show_indicators(self, *args, show_candles=True) -> None:
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
            if arg in self.indicators and not self.indicators[arg].isnull().all():
                if arg == 'SuperTrend':
                    apds.append(mpf.make_addplot(self.indicators[arg], type='line', color='orange'))
                elif arg.startswith('ATR'):
                    apds.append(mpf.make_addplot(self.indicators[arg], secondary_y=True, color='purple'))
                else:
                    apds.append(mpf.make_addplot(self.indicators[arg]))

        if not args:
            for indicator_name in self.indicators.columns:
                if not self.indicators[indicator_name].isnull().all():
                    if indicator_name == 'SuperTrend':
                        apds.append(mpf.make_addplot(self.indicators[indicator_name], secondary_y=False, color='orange'))
                    elif indicator_name.startswith('ATR'):
                        apds.append(mpf.make_addplot(self.indicators[indicator_name], secondary_y=True, color='purple'))
                    else:
                        apds.append(mpf.make_addplot(self.indicators[indicator_name]))

        # 确保OHLCV数据中有有效数据
        if not self.ohlcv_data.empty:
            mpf.plot(self.ohlcv_data, type=plot_type, addplot=apds, volume=True, show_nontrading=True, style='charles')
        else:
            print("OHLCV数据为空, 无法绘图。")


    def show_all_indicators(self) -> None:
        """
        Visualize the OHLCV data with all available indicators.
        """
        # 调用show方法，没有提供指标名，函数会显示所有指标
        self.show_indicators()
