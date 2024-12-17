import pandas as pd
import numpy as np

def icu_ma(close, length=20, sensitivity=2.0, offset=None, **kwargs):
    """
    ICU Moving Average (ICU均线)

    Args:
        close (pd.Series): 价格序列（如收盘价）
        length (int): 基准周期，决定平滑程度，默认20
        sensitivity (float): 波动率敏感系数，决定动态平滑因子的响应速度，默认2.0
        offset (int, optional): 偏移量
        **kwargs: 其他参数，如fillna填充缺失值

    Returns:
        pd.Series: ICU均线序列
    """
    # 参数验证
    close = close if isinstance(close, pd.Series) else pd.Series(close)
    length = int(length) if length > 0 else 20
    sensitivity = float(sensitivity) if sensitivity > 0 else 2.0
    offset = int(offset) if offset else 0
    
    # 计算价格波动率（使用ATR或价格变动）
    price_change = close.diff().abs()  # 绝对价格变动
    volatility = price_change.rolling(window=length).mean()  # 平均波动率（ATR的简化版）
    
    # 计算动态平滑因子（类似EMA的α值）
    max_volatility = volatility.max()  # 获取波动率的最大值作为归一化基准
    smooth_factor = sensitivity * (volatility / max_volatility).clip(lower=0.1, upper=1.0)
    
    # 初始化ICU均线
    icu_ma = pd.Series(np.nan, index=close.index)
    icu_ma.iloc[0] = close.iloc[0]  # 初始化第一个值为收盘价
    
    # 迭代计算ICU均线
    for i in range(1, len(close)):
        alpha = smooth_factor.iloc[i]
        icu_ma.iloc[i] = icu_ma.iloc[i-1] + alpha * (close.iloc[i] - icu_ma.iloc[i-1])
    
    # 偏移处理
    if offset != 0:
        icu_ma = icu_ma.shift(offset)
    
    # 处理缺失值
    fillna = kwargs.get('fillna', None)
    if fillna is not None:
        icu_ma.fillna(fillna, inplace=True)
    
    icu_ma.name = f"ICU_MA_{length}"
    return icu_ma
