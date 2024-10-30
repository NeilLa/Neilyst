# 文件路径：indicators_lib/normalized_stddev.py

import pandas as pd
import numpy as np
from pandas_ta.utils import get_offset, verify_series
from pandas_ta.volatility import atr

def normalized_stddev(high, low, close, std_length=None, atr_length=None, offset=None, **kwargs):
    """
    计算归一化的标准差因子：标准差 / ATR

    参数：
    - high, low, close: 价格序列
    - std_length: 标准差的计算周期
    - atr_length: ATR 的计算周期
    - offset: 偏移量
    """

    # 验证输入数据
    high = verify_series(high)
    low = verify_series(low)
    close = verify_series(close)

    # 设置默认参数
    std_length = int(std_length) if std_length and std_length > 0 else 14
    atr_length = int(atr_length) if atr_length and atr_length > 0 else 14
    offset = get_offset(offset)

    # 计算标准差
    stddev = close.rolling(window=std_length).std()

    # 计算 ATR
    atr_value = atr(high=high, low=low, close=close, length=atr_length)

    # 计算归一化标准差
    normalized_std = stddev / atr_value

    # 处理偏移量
    if offset != 0:
        normalized_std = normalized_std.shift(offset)

    # 处理空值
    if 'fillna' in kwargs:
        normalized_std.fillna(kwargs['fillna'], inplace=True)
    if 'fill_method' in kwargs:
        normalized_std.fillna(method=kwargs['fill_method'], inplace=True)

    # 设置名称
    normalized_std.name = f'Normalized_Std_{std_length}_{atr_length}'

    return normalized_std
