from numpy import nan as npNan
from pandas_ta import Imports
from pandas_ta.utils import get_offset, verify_series

# def ohlc_ema(open, high, low, close, length=None, offset=None, **kwargs):
def ohlc_ema(open, high, low, close, length=None, offset=None, **kwargs):

    """Indicator: EMA of OHLC/4"""
    # Validate Arguments
    length = int(length) if length and length > 0 else 10
    adjust = kwargs.pop('adjust', False)
    sma = kwargs.pop('sma', True)
    open = verify_series(open, length)
    high = verify_series(high, length)
    low = verify_series(low, length)
    close = verify_series(close, length)
    offset = get_offset(offset)

    if open is None or high is None or low is None or close is None:
        return
 
    # Calculate Result
    price = (open + high + low + close) / 4
    ema = price.ewm(span=length, adjust=adjust).mean()
    
    if offset != 0:
        ema = ema.shift(offset)

    # Handle fills
    if 'fillna' in kwargs:
        ema.fillna(kwargs['fillna'], inplace=True)
    if 'fill_method' in kwargs:
        ema.fillna(method=kwargs['fill_method'], inplace=True)

    # Name & Category
    ema.name = f'OHLC_EMA_{length}'
    ema.category = "overlap"

    return ema