import pandas as pd
import numpy as np
from scipy import stats
from typing import Union

def siegelslopes_ma(price_ser: Union[pd.Series, np.ndarray],method:str="hierarchical") -> float:
    """Repeated Median (Siegel 1982)

    Args:
        price_ser (Union[pd.Series, np.ndarray]): index-date values-price or values-price

    Returns:
        float: float
    """
    from scipy import stats
    n: int = len(price_ser)
    res = stats.siegelslopes(price_ser, np.arange(n), method=method)
    return res.intercept + res.slope * (n-1)

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
    
    # 初始化ICU均线
    icu_ma = close.rolling(length).apply(siegelslopes_ma, raw=True)
    
    # 偏移处理
    if offset != 0:
        icu_ma = icu_ma.shift(offset)
    
    # 处理缺失值
    fillna = kwargs.get('fillna', None)
    if fillna is not None:
        icu_ma.fillna(fillna, inplace=True)
    
    icu_ma.name = f"ICU_MA_{length}"
    return icu_ma
