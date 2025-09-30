import pandas as pd
import numpy as np
from pandas_ta.utils import get_offset, verify_series

def amplitude(close, length=None, offset=None, **kwargs):
    """
    Indicator: Amplitude Indicator (基于最近 length 根 K 线的最高收盘价与最低收盘价)
    
    计算公式：
        振幅 = 100 * ( 最高收盘价 - 最低收盘价 ) / 最低收盘价
    
    Args:
        close (pd.Series): 收盘价序列
        length (int, optional): 回溯的K线数量。默认 20
        offset (int, optional): 结果偏移量。默认 None
        **kwargs: 其他可选参数：
            - fillna (value): 使用此 value 填充缺失值
            - fill_method (str): 使用此方法填充缺失值 (ffill, bfill)
    
    Returns:
        pd.Series: 振幅指标序列 (单位:%)
    """
    
    # 1. 参数校验
    length = int(length) if length and length > 0 else 20
    close = verify_series(close, length)  # 来自 pandas_ta.utils，用于校验序列
    offset = get_offset(offset)

    if close is None:
        return

    # 2. 计算最高价、最低价
    # 注意：这里使用 rolling(window=length).max() / min() 时，默认提取的是这段时间内的最高/最低收盘价
    rolling_max = close.rolling(window=length).max()
    rolling_min = close.rolling(window=length).min()
    
    # 3. 计算振幅: 100 * (highest - lowest) / lowest
    # 对于最低值为0的情况，这里不做特殊处理，如需要可自行额外判断
    amplitude = 100 * (rolling_max - rolling_min) / rolling_min
    
    # 4. 处理 offset
    if offset != 0:
        amplitude = amplitude.shift(offset)
    
    # 5. 处理缺失值
    fillna = kwargs.get('fillna', None)
    fill_method = kwargs.get('fill_method', None)
    
    if fillna is not None:
        amplitude.fillna(fillna, inplace=True)
    if fill_method is not None:
        amplitude.fillna(method=fill_method, inplace=True)
    
    # 6. 命名
    amplitude.name = f'AMPLITUDE_{length}'
    
    return amplitude
