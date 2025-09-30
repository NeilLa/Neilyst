from pandas import Series
# some utils function from pandas ta
# for helping my own indicators calculation

def verify_series(series, min_length=None):
    # if a series and it meets the min_length of the indicators return it
    has_length = min_length is not None and isinstance(min_length, int)
    if series is not None and isinstance(series, Series):
        return None if has_length and series.size < min_length else series