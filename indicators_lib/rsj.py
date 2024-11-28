from numpy import nan as npNan
from pandas_ta import Imports
from pandas_ta.utils import get_offset, verify_series

def rsj(close, length=None, offset=None, **kwargs):
    """Indicator: Relative Signed Jump (RSJ)"""

    # Validate Arguments
    length = int(length) if length and length > 0 else 10
    close = verify_series(close, length)
    offset = get_offset(offset)

    if close is None:
        return

    # Calculate Returns
    returns = close.pct_change()

    # Calculate realized variance over the window
    rv = returns.rolling(window=length).var()

    # Functions to compute variance of positive and negative returns
    def var_positive(x):
        positive_x = x[x > 0]
        if len(positive_x) > 0:
            return positive_x.var()
        else:
            return npNan

    def var_negative(x):
        negative_x = x[x < 0]
        if len(negative_x) > 0:
            return negative_x.var()
        else:
            return npNan

    # Compute rv_p and rv_n using rolling apply
    rv_p = returns.rolling(window=length).apply(var_positive, raw=False)
    rv_n = returns.rolling(window=length).apply(var_negative, raw=False)

    # Compute RSJ
    rsj = (rv_p - rv_n) / rv

    # Offset
    if offset != 0:
        rsj = rsj.shift(offset)

    # Handle fills
    if 'fillna' in kwargs:
        rsj.fillna(kwargs['fillna'], inplace=True)
    if 'fill_method' in kwargs:
        rsj.fillna(method=kwargs['fill_method'], inplace=True)

    # Name & Category
    rsj.name = f'RSJ_{length}'
    rsj.category = 'volatility'

    return rsj
