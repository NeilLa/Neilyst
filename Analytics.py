from DataManager import Fetcher
import pandas as pd
import mplfinance as mpf
from scipy.stats import linregress

class Indicators(Fetcher):
    def __init__(self, exchange_name) -> None:
        super().__init__(exchange_name)

    def __set_index(self) -> None:
        self.indicators = pd.DataFrame(index=self.ohlcv_data.index)

    def MAX(self, l) -> None:
        """
        Calculate the Max value for the high price.
        l: Length of the window for the max window.
        """

        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")
        
        if self.indicators is None:
            self.__set_index()

        self.indicators[f'MAX{l}'] = self.ohlcv_data['high'].rolling(window=l).max()
    
    def MIN(self, l) -> None:
        """
        Calculate the Min value for the low price.
        l: Length of the window for the max window.
        """

        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")
        
        if self.indicators is None:
            self.__set_index()

        self.indicators[f'MIN{l}'] = self.ohlcv_data['low'].rolling(window=l).max()
        
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

        """
        使用收盘价和移动平均线回归
        市场趋势反映：这种方法关注的是收盘价与其移动平均线之间的关系，可以视为市场价格与其近期趋势之间的相对强度。
        适用性：如果您的策略重点是捕捉基于价格趋势的动态，那么这种方法可能更适用。
        平稳性：收盘价通常比高低价更平稳，这可能使得基于它的回归分析结果更加稳定。

        使用最高价和最低价回归
        价格波动捕捉：这种方法通过分析最高价和最低价之间的关系，旨在捕捉市场在特定周期内的波动性。
        适用性：如果您的策略更侧重于识别市场的波动范围和潜在的反转点，这种方法可能更合适。
        反应性：最高价和最低价能够更快地反应市场的极端变化，这可能对于寻找交易机会或风险管理特别有价值。
        """
        
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

    def SuperTrend(self, atr_length=22, atr_multiplier=3.0, wicks=True):
        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")

        if self.indicators is None:
            self.__set_index()

        # 计算 ATR
        self.ATR(atr_length)
        atr = self.indicators[f'ATR{atr_length}'] * atr_multiplier

        # 高低价选择
        highPrice = self.ohlcv_data['high'] if wicks else self.ohlcv_data['close']
        lowPrice = self.ohlcv_data['low'] if wicks else self.ohlcv_data['close']
        hl2 = (highPrice + lowPrice) / 2

        # 初始化长停和短停
        longStop = hl2 - atr
        shortStop = hl2 + atr

        # 初始化趋势方向
        trendDirection = False
        superTrend = []

        for i in range(len(self.ohlcv_data)):
            doji = self.ohlcv_data['open'][i] == self.ohlcv_data['close'][i] == self.ohlcv_data['high'][i] == self.ohlcv_data['low'][i]

            if i == 0:
                superTrend.append(longStop[i])
                longStopPrev = longStop[i]
                shortStopPrev = shortStop[i]
            else:
                # 考虑前一个点的长停和短停值
                longStop[i] = longStop[i] if doji else max(longStop[i], longStopPrev) if lowPrice[i - 1] > longStopPrev else longStop[i]
                shortStop[i] = shortStop[i] if doji else min(shortStop[i], shortStopPrev) if highPrice[i - 1] < shortStopPrev else shortStop[i]

                # 更新趋势方向
                if not trendDirection and self.ohlcv_data['close'][i] > shortStopPrev:
                    trendDirection = True
                elif trendDirection and self.ohlcv_data['close'][i] < longStopPrev:
                    trendDirection = False

                # 添加到 SuperTrend 列表
                superTrend.append(longStop[i] if trendDirection else shortStop[i])

                # 更新前一个点的值
                longStopPrev = longStop[i]
                shortStopPrev = shortStop[i]

        self.indicators['SuperTrend'] = pd.Series(superTrend, index=self.ohlcv_data.index)


    def PVT(self, ema_length=21):
        """
        Calculate the Price Volume Trend (PVT) indicator and its EMA signal line.

        ema_length: Length of the EMA window for the signal line.
        """
        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")

        if self.indicators is None:
            self.__set_index()

        # 初始化PVT指标
        self.indicators['PVT'] = 0

        # 计算PVT
        for i in range(1, len(self.ohlcv_data)):
            price_change_ratio = (self.ohlcv_data['close'][i] - self.ohlcv_data['close'][i - 1]) / self.ohlcv_data['close'][i - 1]
            self.indicators['PVT'][i] = self.indicators['PVT'][i - 1] + (price_change_ratio * self.ohlcv_data['volume'][i])

        # 填充第一个值为0
        self.indicators['PVT'][0] = 0

        # 计算PVT的EMA信号线
        self.indicators['PVT_EMA'] = self.indicators['PVT'].ewm(span=ema_length, adjust=False).mean()

    def VolatilityMA(self, l = 20):
        """
        Calculate the Volatility and MA Volatility.
        """
        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")

        if self.indicators is None:
            self.__set_index()

        spike = self.ohlcv_data['close'] - self.ohlcv_data['open']
        self.indicators['Volatility'] = spike.abs()
        self.indicators['VolatilityMA'] = self.indicators['Volatility'].rolling(window=l).mean()

    def KDJ(self, n=9, m=3):
        """
        Calculate the KDJ indicator.

        n: The lookback period to calculate RSV.
        m: The smoothing period for K and D lines.
        """
        if self.ohlcv_data is None:
            raise ValueError("OHLCV data not available for calculation!")

        if self.indicators is None:
            self.__set_index()

        low_list = self.ohlcv_data['low'].rolling(n, min_periods=1).min()
        high_list = self.ohlcv_data['high'].rolling(n, min_periods=1).max()
        rsv = (self.ohlcv_data['close'] - low_list) / (high_list - low_list) * 100

        self.indicators['K'] = rsv.ewm(alpha=1/m, adjust=False).mean()
        self.indicators['D'] = self.indicators['K'].ewm(alpha=1/m, adjust=False).mean()
        self.indicators['J'] = 3 * self.indicators['K'] - 2 * self.indicators['D']
        
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
