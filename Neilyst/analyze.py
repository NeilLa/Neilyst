# 本模块是对策略实盘交易历史的分析工具

import pandas as pd
from .utils.magic import PNL_THRESHOLD

def load_history(path):
    history = pd.read_csv(path)
    history['时间'] = pd.to_datetime(history['时间'])
    return history

def calculate_win_rate(df, periods=None, symbol=None):
    df = _filter_close_order(df)

    if periods and symbol:
        return _calculate_win_rate_over_periods(df, periods, symbol)
    
    elif periods:
        symbol_win_rates = {}
        symbols = df['产品名称'].unique()

        overall_win_rate = _calculate_win_rate_over_periods(df, periods)

        for sym in symbols:
            sym_win_rate = _calculate_win_rate_over_periods(df, periods, sym)
            symbol_win_rates[sym] = sym_win_rate
        
        symbol_win_rates['overall'] = overall_win_rate
        return symbol_win_rates
    
    elif symbol:
        return _calculate_win_rate_over_periods(df, [(df['时间'].min(), df['时间'].max())], symbol)
    
    else:
        return _calculate_win_rate_over_periods(df, [(df['时间'].min(), df['时间'].max())])

def _calculate_win_rate_over_periods(df, periods, symbol=None):
    totals_wins = 0
    totals_trades = 0

    for start, end in periods:
        periods_df = _filter_by_date(df, start, end)
        if symbol:
            periods_df = _filter_by_symbol(periods_df, symbol)
        
        wins = len(periods_df[periods_df['收益'] > 0])
        totals_wins += wins
        totals_trades += len(periods_df)

    overall_win_rate = totals_wins / totals_trades if totals_trades > 0 else 0
    return overall_win_rate

def _filter_by_date(df, start, end):
    mask = (df['时间'] >= start) & (df['时间'] < end)
    return df.loc[mask]

def _filter_by_symbol(df, symbol):
    mask = (df['产品名称'] == symbol)
    return df.loc[mask]

def _filter_close_order(df):
    mask = abs(df['收益']) > PNL_THRESHOLD
    return df.loc[mask]