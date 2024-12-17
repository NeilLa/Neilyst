import pandas as pd
import numpy as np
from numpy import nan as npNan
from pandas_ta.utils import get_offset, verify_series

def bollinger_k(close, length=None, offset=None, **kwargs):
    """
    Indicator: Bollinger Band K Value (Number of Standard Deviations from Moving Average)

    Args:
        close (pd.Series): Close price series
        length (int, optional): Period for MA and STD calculation. Default: 20
        offset (int, optional): Offset for the result
        **kwargs: Additional keyword arguments:
            - ma_type (str): Type of moving average ('sma', 'ema', etc.). Default: 'sma'
            - fillna (value): Fill NA values with this value
            - fill_method (str): Method to fill NA values

    Returns:
        pd.Series: K value series indicating how many standard deviations the close price is from the moving average
    """
    
    # Validate Arguments
    length = int(length) if length and length > 0 else 20
    close = verify_series(close, length)
    offset = get_offset(offset)
    ma_type = kwargs.pop('ma_type', 'sma').lower()
    
    if close is None:
        return
    
    # Calculate Moving Average
    if ma_type == 'ema':
        ma = close.ewm(span=length, adjust=False).mean()
    elif ma_type == 'wma':
        weights = np.arange(1, length + 1)
        ma = close.rolling(length).apply(lambda prices: np.dot(prices, weights)/weights.sum(), raw=True)
    else:  # Default to SMA
        ma = close.rolling(window=length).mean()
    
    # Calculate Standard Deviation
    std = close.rolling(window=length).std()
    
    # Calculate K Value
    k_value = (close - ma) / std

    # Average K Value
    # k_value = k_value.rolling(window=length).mean()
    
    # Apply offset
    if offset != 0:
        k_value = k_value.shift(offset)
    
    # Handle fills
    fillna = kwargs.get('fillna', None)
    fill_method = kwargs.get('fill_method', None)
    
    if fillna is not None:
        k_value.fillna(fillna, inplace=True)
    if fill_method is not None:
        k_value.fillna(method=fill_method, inplace=True)
    
    # Name & Category
    k_value.name = f'BOLL_K_{length}'
    # k_value.category = "volatility"  # 如果需要分类，可以自行添加
    
    return k_value
