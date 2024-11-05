from numpy import nan as npNaN
from pandas_ta.utils import get_offset, verify_series
import pandas as pd

def rsrs(high, low, length=None, std_length=None, offset=None, **kwargs):
    """Indicator: Relative Strength Rank Slope (RSRS)
    
    返回两个列：
    - RSRS_Beta：原始斜率 β
    - RSRS：标准化后的 RSRS 值
    """
    # 验证参数
    length = int(length) if length and length > 0 else 18
    std_length = int(std_length) if std_length and length > 0 else 600
    high = verify_series(high)
    low = verify_series(low)
    offset = get_offset(offset)

    if high is None or low is None:
        return

    # 将 low 和 high 合并为 DataFrame
    hl_df = pd.concat([low, high], axis=1)
    hl_df.columns = ['low', 'high']

    # 初始化一个空的列表来存储 β 值
    beta_values = [npNaN] * len(hl_df)

    # 计算滚动斜率 β
    for i in range(length - 1, len(hl_df)):
        hl_window = hl_df.iloc[i - length + 1:i + 1]
        x = hl_window['low'].values
        y = hl_window['high'].values

        x_mean = x.mean()
        y_mean = y.mean()
        numerator = ((x - x_mean) * (y - y_mean)).sum()
        denominator = ((x - x_mean) ** 2).sum()
        if denominator == 0:
            beta = npNaN
        else:
            beta = numerator / denominator

        beta_values[i] = beta

    # 将 β 值转换为 Series
    beta = pd.Series(beta_values, index=hl_df.index)

    # 计算 β 的滚动均值和标准差
    beta_mean = beta.rolling(window=std_length, min_periods=1).mean()
    beta_std = beta.rolling(window=std_length, min_periods=1).std()

    # 计算标准化后的 RSRS 值
    rsrs = (beta - beta_mean) / beta_std

    # 处理偏移量
    if offset != 0:
        beta = beta.shift(offset)
        rsrs = rsrs.shift(offset)

    # 处理缺失值
    if "fillna" in kwargs:
        beta.fillna(kwargs["fillna"], inplace=True)
        rsrs.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        beta.fillna(method=kwargs["fill_method"], inplace=True)
        rsrs.fillna(method=kwargs["fill_method"], inplace=True)

    # 设置名称和分类
    beta.name = f"RSRS_Beta_{length}"
    rsrs.name = f"RSRS_{length}_{std_length}"
    beta.category = rsrs.category = "volatility"

    # 将结果合并为 DataFrame
    rsrs_df = pd.concat([beta, rsrs], axis=1)

    return rsrs_df
