# 本模块是对策略实盘交易历史的分析工具

import pandas as pd
from .utils.magic import PNL_THRESHOLD

def load_history(path):
    # 加载账单数据
    history = pd.read_csv(path)
    history['时间'] = pd.to_datetime(history['时间'])
    return history

def calculate_profit_loss_ratio(df, periods=None, symbol=None):
    """
      对外的盈亏比计算接口, 统计交易账单中的盈亏比
    """
    df = _filter_close_order(df)



def calculate_trade_counts(df, periods=None, symbol=None):
    pass

def calculate_win_rate(df, periods=None, symbol=None):
    """
      对外的计算胜率接口, 统计交易账单中的胜率
    
    Parameters
    ------
      periods: list
        起止时间列表, list中每个元素都是一个tuple, 每个tuple中包括了起止时间
        如果这个参数为None, 则计算全时间内的胜率
      symbol: string
        需要计算胜率的标的, 如果这个参数为None, 则计算全币种的胜率, 以及每种交易对的胜率
    """
    df = _filter_close_order(df)

    if periods and symbol:
        return _calculate_win_rate_over_periods(df, periods, symbol)
    
    elif periods:
        return _calculate_win_rate_overall_symbols(df, periods)
    
    elif symbol:
        return _calculate_win_rate_over_periods(df, [(df['时间'].min(), df['时间'].max())], symbol)
    
    else:
        return _calculate_win_rate_over_periods(df, [(df['时间'].min(), df['时间'].max())])

def _calculate_win_rate_overall_symbols(df, periods):
    symbol_win_rate = {}
    symbols = df['产品名称'].unique()

    overall_win_rate = _calculate_win_rate_over_periods(df, periods)

    for sym in symbols:
        sym_win_rate = _calculate_win_rate_over_periods(df, periods, sym)
        symbol_win_rate[sym] = sym_win_rate
    
    sym_win_rate['overall'] = overall_win_rate
    
    return sym_win_rate

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

def _calculate_profit_loss_ratio(df, periods, symbol=None):
    pass

def _filter_by_date(df, start, end):
    mask = (df['时间'] >= start) & (df['时间'] < end)
    return df.loc[mask]

def _filter_by_symbol(df, symbol):
    mask = (df['产品名称'] == symbol)
    return df.loc[mask]

def _filter_close_order(df):
    # 过滤掉非平仓数据
    # 账单中开仓的收益为小数点后八个零, 但不为0
    # 所以需要这样过滤
    mask = abs(df['收益']) > PNL_THRESHOLD
    return df.loc[mask]