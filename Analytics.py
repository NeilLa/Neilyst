from DataManager import Fetcher
import pandas as pd
import mplfinance as mpf
from scipy.stats import linregress

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
    
    def VolumeMA(self, l) -> None:
        """
        Calculate the Moving Average of Volume for the given length 'l'.

        l: Length of the window for the moving average.

        """

        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")
        
        if self.indicators is None:
            self.__set_index()

        ma_series = self.ohlcv_data['volume'].rolling(window=l).mean()
        # Forward fill the NaN values
        ma_series_filled = ma_series.fillna(method='bfill')
    
        self.indicators[f'VolumeMA{l}'] = ma_series_filled

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
    

    def Boll(self, l=20, n_std=2):
        """
        Calculate Bollinger Bands.

        l: Length of the window for the moving average.
        n_std: Number of standard deviations from the moving average.
        """
        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")

        if self.indicators is None:
            self.__set_index()

        # 计算中间线，即简单移动平均线
        middle_band = self.ohlcv_data['close'].rolling(window=l).mean()

        # 计算标准差
        std = self.ohlcv_data['close'].rolling(window=l).std()

        # 计算上下轨
        upper_band = middle_band + (n_std * std)
        lower_band = middle_band - (n_std * std)

        # 将布林带添加到指标数据中
        self.indicators['Bollinger_upper'] = upper_band
        self.indicators['Bollinger_middle'] = middle_band
        self.indicators['Bollinger_lower'] = lower_band
    
    def RSI(self, period=14):
        """
        Calculate the Relative Strength Index (RSI).

        period: The number of periods to calculate the RSI over.
        """
        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")

        if self.indicators is None:
            self.__set_index()

        # 计算价格变化
        delta = self.ohlcv_data['close'].diff()

        # 计算涨跌幅度
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 计算平均涨跌幅度
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        # 计算相对强度（RS）
        rs = avg_gain / avg_loss

        # 计算RSI
        rsi = 100 - (100 / (1 + rs))

        # 将RSI添加到指标数据中
        self.indicators[f'RSI{period}'] = rsi.fillna(0)

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
    
    def RSRS(self, l=18, max_window=250, method= 'high/low'):
        """
        Calculate the Relative Strength Regression Score (RSRS) with proper standardization.

        l: Length of the window for the regression analysis.

        method: Parameter selection of OLS, if method=high/low, then use the high price and low price for regression. Otherwise, method=close/ma, we will use the close price and close ma for regression.
        """
        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")

        if self.indicators is None:
            self.__set_index()

        # 初始化RSRS指标数组
        rsrs = pd.Series(index=self.ohlcv_data.index)
        rsrs_standardized = pd.Series(index=self.ohlcv_data.index)

        # 遍历数据并计算每个窗口的RSRS
        for i in range(l - 1, len(self.ohlcv_data)):
            if method == 'high/low':
                window_high = self.ohlcv_data['high'][i - l + 1:i + 1]
                window_low = self.ohlcv_data['low'][i - l + 1:i + 1]
                slope, _, _, _, _ = linregress(window_high, window_low)

            elif method == 'close/ma':
                window_prices = self.ohlcv_data['close'][i - l + 1:i + 1]
                window_ma = self.ohlcv_data['close'].rolling(window=l).mean()[i - l + 1:i + 1]
                slope, _, _, _, _ = linregress(window_prices, window_ma)

            # 存储RSRS值
            rsrs[i] = slope

            # 标准化处理（使用截至当前的数据
            # 请注意，这种标准化方法与原论文中不同
            # 原论文中使用了未来函数，使得RSRS在全局上进行标准化
            # 而我没有使用这种思路
            # 全局标准化可能会有更好的回测结果，但并不能用于实盘交易
            # 本方法可能会导致在数据集的初始阶段RSRS值较为敏感
            # 因此在分析时需要特别注意
            start = max(0, i - max_window + 1)
            rsrs_mean = rsrs[start:i + 1].mean()
            rsrs_std = rsrs[start:i + 1].std()
            rsrs_standardized[i] = (rsrs[i] - rsrs_mean) / rsrs_std

        # 将标准化后的RSRS值添加到指标数据中
        self.indicators['RSRS_standardized'] = rsrs_standardized

        # 将原始RSRS值也加入指标中
        self.indicators['RSRS'] = rsrs

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
