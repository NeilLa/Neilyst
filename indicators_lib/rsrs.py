import pandas as pd
from numpy import nan as npNaN
from pandas_ta.utils import get_offset, verify_series

def rsrs(high, low, close, length=None, std_length=None, offset=None, **kwargs):
    """
    计算 RSRS 指标，包括原始 RSRS、标准化 RSRS、钝化 RSRS。

    返回包含以下列的 DataFrame：
    - RSRS_Beta：原始斜率 β
    - RSRS：标准化后的 RSRS 值
    - RSRS_Passive：钝化 RSRS 值
    """
    # 验证参数
    length = int(length) if length and length > 0 else 18
    std_length = int(std_length) if std_length and std_length > 0 else 300  # 根据您的需要调整
    offset = get_offset(offset)

    high = verify_series(high)
    low = verify_series(low)
    close = verify_series(close)

    if high is None or low is None or close is None or open is None:
        return

    # 初始化 DataFrame
    hl_df = pd.concat([low, high], axis=1)
    hl_df.columns = ['low', 'high']

    # 初始化用于存储 β 和 R 方的列表
    beta_values = [npNaN] * len(hl_df)
    r2_values = [npNaN] * len(hl_df)

    # 计算滚动斜率 β 和 R 方
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
            r_squared = npNaN
        else:
            beta = numerator / denominator
            y_pred = x * beta + (y_mean - beta * x_mean)
            ss_res = ((y - y_pred) ** 2).sum()
            ss_tot = ((y - y_mean) ** 2).sum()
            r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else npNaN

        beta_values[i] = beta
        r2_values[i] = r_squared

    # 将 β 和 R 方转换为 Series
    beta = pd.Series(beta_values, index=hl_df.index)
    r_squared = pd.Series(r2_values, index=hl_df.index)

    # 计算标准化 RSRS
    beta_mean = beta.rolling(window=std_length, min_periods=1).mean()
    beta_std = beta.rolling(window=std_length, min_periods=1).std()
    rsrs = (beta - beta_mean) / beta_std

    # 计算收益率标准差的分位数（ret_quantile）
    N = length  # 使用与 β 相同的 N
    M = std_length  # 使用与标准化相同的 M
    returns = close.pct_change()
    ret_std = returns.rolling(window=N).std()
    # 计算过去 M 期内标准差的分位数
    ret_quantile = ret_std.rolling(window=M).apply(
        lambda x: x.rank(pct=True)[-1] if len(x.dropna()) == M else npNaN, raw=False)

    # 计算钝化 RSRS
    rsrs_passive = rsrs * (r_squared ** (2 * ret_quantile))

    # 处理偏移量
    if offset != 0:
        beta = beta.shift(offset)
        rsrs = rsrs.shift(offset)
        rsrs_passive = rsrs_passive.shift(offset)

    # 处理缺失值
    if "fillna" in kwargs:
        beta.fillna(kwargs["fillna"], inplace=True)
        rsrs.fillna(kwargs["fillna"], inplace=True)
        rsrs_passive.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        beta.fillna(method=kwargs["fill_method"], inplace=True)
        rsrs.fillna(method=kwargs["fill_method"], inplace=True)
        rsrs_passive.fillna(method=kwargs["fill_method"], inplace=True)

    # 设置名称和分类
    beta.name = f"RSRS_Beta_{length}"
    rsrs.name = f"RSRS_{length}_{std_length}"
    rsrs_passive.name = f"RSRS_Passive_{length}_{std_length}"
    beta.category = rsrs.category = rsrs_passive.category = "volatility"

    # 将结果合并为 DataFrame
    rsrs_df = pd.concat([beta, rsrs, rsrs_passive], axis=1)

    return rsrs_df
