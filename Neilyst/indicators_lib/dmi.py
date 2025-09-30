import pandas as pd
import numpy as np
from ..utils import verify_series

def dmi(high, low, close, length=None, lensig=None, scalar=None, mamode=None, drift=None, offset=None, **kwargs):
    # Validate Arguments
    length = length if length else 14
    high = verify_series(high, length)
    low = verify_series(low, length)
    close = verify_series(close, length)

    if high is None or low is None or close is None: return

    # Calculate Result
    
    