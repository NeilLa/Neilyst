import pandas as pd
import numpy as np
from tqdm import tqdm
import datetime
import matplotlib.pyplot as plt
from .data import get_klines
from .models import Position
from .utils.magic import US_TREASURY_YIELD, DAYS_IN_ONE_YEAR, TRADING_DAYS_IN_ONE_YEAR, TIMEZONE

def backtest(symbol, start, end, strategy, proxy='http://127.0.0.1:7890/'):
    ## 目前没有考虑双向持仓

    # 本函数是对外的回测接口函数
    # 通过接受symbol寻找文件夹中是否有1min级别数据
    # 用此数据来模拟ticker数据进行回测
    # start, end是回测的起止时间
    # strategy是标准的策略对象

    # strategy应该是一个对象
    # 初始金额，手续费，滑点模拟比率由构造函数初始化
    # run方法将会返回一个对象或者是None

    # 回测引擎应该维护一个历史仓位账单，包括每次开平仓价格，确定盈亏，仓位数量，开仓方向
    # 还应该维护一个当前仓位，保存开仓价，方向，数量，浮盈等等

    # 这是针对单个币种进行择时，若是对多币种进行回测
    # 多币种回测目前有两种情况一种是多个币运行同一个策略。这种情况主要重点在统计结果
    # 另一种是同一个策略里包含多个币种，这样传入的symbol似乎是一个list
    # 可以考虑使用一个新的内部函数作为这种情况的驱动引擎

    # 由于backtest也需要拉取数据 所以也添加一个proxy变量

    # 判断是单币种还是多币种策略

    if isinstance(symbol, str):
        result = []
        # 运行回测引擎得到结果
        result = _single_symbol_engine(symbol, start, end, strategy, proxy)
        # 修改回测账单时区
        result = _convert_result_time(result, TIMEZONE)
        
    elif isinstance(symbol, list):
        result = {}
        result = _multi_symbol_engine(symbol, start, end, strategy, proxy)

    return result

def _single_symbol_engine(symbol, start, end, strategy, proxy):
    # 获取1min数据
    ticker_data = get_klines(symbol, start, end, '1m', proxy=proxy)
    # 初始化仓位历史记录
    current_pos = Position(symbol)
    pos_history = []
    
    # 初始化策略参数
    current_balance = strategy.total_balance
    trading_fee_ratio = strategy.trading_fee_ratio
    slippage_ratio = strategy.slippage_ratio

    for index, row in tqdm(ticker_data.iterrows(), total=ticker_data.shape[0]):
        # 先根据当前价格更新仓位的浮动盈亏
        current_pos.update_float_profit(row['close'])
        
        # 从策略函数获取策略信号
        signal = strategy.run(index, row, current_pos, current_balance, symbol)

        if signal is not None:
            # 初始化交易成本
            trade_cost = 0 # 包括手续费和模拟滑点损耗
            # 开仓逻辑
            if signal.dir == 'long' or signal.dir == 'short':
                # 计算交易成本
                trade_cost = signal.amount * signal.price * (trading_fee_ratio + slippage_ratio)
                # 执行开平仓操作
                current_pos.open(signal.price, signal.amount, signal.dir, index)
                if signal.dir == 'long':
                    current_balance -= signal.amount * signal.price + trade_cost
                elif signal.dir == 'short':
                    current_balance += signal.amount * signal.price + trade_cost
            elif signal.dir == 'close':
                close_amount = min(signal.amount, current_pos.amount)
                if close_amount > 0:
                    trade_cost = close_amount * signal.price * (trading_fee_ratio + slippage_ratio)
                    if current_pos.dir == 'long':
                        current_balance += close_amount * signal.price - trade_cost
                    elif current_pos.dir == 'short':
                        current_balance -= signal.price * close_amount - trade_cost
                    current_pos.close(signal.price, close_amount, index)

                # 如果完全平仓，则视为本次交易结束
                if current_pos.amount == 0:
                    # 记录仓位
                    pos_history.append({
                        'open_date': current_pos.open_date,
                        'close_date': current_pos.close_date,
                        'dir': current_pos.dir,
                        'open_price': current_pos.open_price,
                        'close_price': current_pos.close_price,
                        'amount': abs(current_pos.pnl / (current_pos.open_price - current_pos.close_price)),
                        'pnl': current_pos.pnl,
                        'balance': current_balance
                    })

                    # 重新初始化pos对象
                    current_pos = Position(symbol)

    # 整体回测结束，平掉所有仓位
    if current_pos.amount > 0:
        final_price = ticker_data.iloc[-1]['close']
        current_pos.close(final_price, current_pos.amount, ticker_data.index[-1])
        trade_cost = current_pos.amount * final_price * (trading_fee_ratio + slippage_ratio)

        # 计算最终余额
        if current_pos.dir == 'long':
            current_balance += current_pos.amount * final_price - trade_cost
        elif current_pos.dir == 'short':
            current_balance -= (current_pos.open_price - final_price) * current_pos.amount
        
        # 记录最后仓位
        pos_history.append({
            'open_date': current_pos.open_date,
            'close_date': current_pos.close_date,
            'dir': current_pos.dir,
            'open_price': current_pos.open_price,
            'close_price': current_pos.close_price,
            'amount': abs(current_pos.pnl / (current_pos.open_price - current_pos.close_price)),
            'pnl': current_pos.pnl,
            'balance': current_balance  
        })
        
    return pos_history

def _multi_symbol_engine(symbols, start, end, strategy, proxy):
    pos_historys = dict()
    for symbol in symbols:
        pos_historys[symbol] = _single_symbol_engine(symbol, start, end, strategy, proxy)
        pos_historys[symbol] = _convert_result_time(pos_historys[symbol], TIMEZONE)
    
    return pos_historys

def _convert_result_time(result, timedelta):
    """
    由于ccxt的默认时间为0时区, 所以为了更好地对比回测账单和实盘账单
    新增该函数用以调整回测账单的时区
    timedelta即为时区修正的小时数
    eg: timedelta=8 => UTG+8
    """
    if not result:
        print("No result now!")
        return
    
    updated_result = []
    for entry in result:
        updated_entry = entry.copy()

        if 'open_date' in updated_entry:
            updated_entry['open_date'] = updated_entry['open_date'] + datetime.timedelta(hours=timedelta)
        if 'close_date' in updated_entry:
            updated_entry['close_date'] = updated_entry['close_date'] + datetime.timedelta(hours=timedelta)
        
        updated_result.append(updated_entry)
    
    return updated_result

def evaluate_strategy(result, init_balance, risk_free_rate=US_TREASURY_YIELD):
    """
    评估策略的绩效指标，支持单 symbol 和多 symbol。
    
    参数:
    - result: 单 symbol 时为 list，多 symbol 时为 dict。
    - init_balance: 初始资金。
    - risk_free_rate: 无风险利率，默认为美国国债收益率。
    
    返回:
    - 一个包含总收益、胜率、盈亏比、最大回撤、年化收益率、夏普比率等指标的字典。
    """
    
    # 如果是单 symbol，直接转换为 DataFrame 进行计算
    if isinstance(result, list):
        return _evaluate_single_symbol(result, init_balance, risk_free_rate)
    
    # 如果是多 symbol，分别计算每个 symbol 的绩效，并汇总总的结果
    elif isinstance(result, dict):
        total_stats = _initialize_stats()

        total_trades = 0  # 记录总交易次数，用于加权平均
        earliest_start_date = None
        latest_end_date = None

        for _, history in result.items():
            symbol_stats = _evaluate_single_symbol(history, init_balance, risk_free_rate)
            total_trades += len(history)
            total_trades += symbol_stats['total_trades']

            # 更新最早开始日期和最晚结束日期
            if earliest_start_date is None or symbol_stats['start_date'] < earliest_start_date:
                earliest_start_date = symbol_stats['start_date']
            if latest_end_date is None or symbol_stats['end_date'] > latest_end_date:
                latest_end_date = symbol_stats['end_date']
            
            # 累积每个 symbol 的绩效指标（按交易次数加权平均）
            total_stats = _accumulate_stats(total_stats, symbol_stats, len(history))
        
        # 计算总的交易天数
        total_days = (latest_end_date - earliest_start_date).days + 1 if earliest_start_date and latest_end_date else 1

        # 计算加权平均的结果
        total_stats = _finalize_stats(total_stats, total_trades)

        # 添加总交易次数和平均每日交易次数
        total_stats['total_trades'] = total_trades
        total_stats['average_daily_trades'] = total_trades / total_days if total_days > 0 else 0
        
        return total_stats

    else:
        raise ValueError("Invalid result format. Expected list or dict.")


def _evaluate_single_symbol(history, init_balance, risk_free_rate=US_TREASURY_YIELD):
    """
    评估单个 symbol 的绩效指标。
    
    参数:
    - history: 包含该 symbol 的交易历史。
    - init_balance: 初始资金。
    - risk_free_rate: 无风险利率。
    
    返回:
    - 一个包含总收益、胜率、盈亏比、最大回撤、年化收益率、夏普比率、交易次数、日均交易次数等指标的字典。
    """
    
    df = pd.DataFrame(history)

    if df.empty:
        print('No trading result')
        return
    
    # 计算交易次数
    total_trades = len(df)

    # 计算交易期间的天数
    start_date = df['open_date'].iloc[0]
    end_date = df['close_date'].iloc[-1]
    total_days = (end_date - start_date).days + 1  # 加1以包含开始和结束日期

    # 计算日均交易次数
    average_daily_trades = total_trades / total_days if total_days > 0 else 0
    
    # 计算各项指标
    total_pnl = df['pnl'].sum()
    win_rate = _calculate_win_rate(df)
    profit_loss_ratio = _calculate_profit_loss_ratio(df)
    max_drawdown = _calculate_max_drawdown(df['pnl'])
    annual_return = _calculate_annual_return(df, init_balance, total_pnl)
    sharpe_ratio = _calculate_sharpe_ratio(df, init_balance, risk_free_rate)
    
    return {
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'profit_loss_ratio': profit_loss_ratio,
        'max_drawdown': max_drawdown,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'total_trades': total_trades,
        'average_daily_trades': average_daily_trades,
        'start_date': start_date,
        'end_date': end_date
    }

# 初始化统计结果的函数
def _initialize_stats():
    return {
        'total_pnl': 0,
        'win_rate': 0,
        'profit_loss_ratio': 0,
        'max_drawdown': 0,
        'annual_return': 0,
        'sharpe_ratio': 0
    }

# 累积多 symbol 结果
def _accumulate_stats(total_stats, symbol_stats, num_trades):
    total_stats['total_pnl'] += symbol_stats['total_pnl']
    total_stats['win_rate'] += symbol_stats['win_rate'] * num_trades
    total_stats['profit_loss_ratio'] += symbol_stats['profit_loss_ratio'] * num_trades
    total_stats['max_drawdown'] += symbol_stats['max_drawdown'] * num_trades
    total_stats['annual_return'] += symbol_stats['annual_return'] * num_trades
    total_stats['sharpe_ratio'] += symbol_stats['sharpe_ratio'] * num_trades
    return total_stats

# 最终计算加权平均的结果
def _finalize_stats(total_stats, total_trades):
    if total_trades > 0:
        total_stats['win_rate'] /= total_trades
        total_stats['profit_loss_ratio'] /= total_trades
        total_stats['max_drawdown'] /= total_trades
        total_stats['annual_return'] /= total_trades
        total_stats['sharpe_ratio'] /= total_trades
    return total_stats

# 各个指标的计算函数

def _calculate_win_rate(df):
    """ 计算胜率 """
    return (df['pnl'] > 0).mean()

def _calculate_profit_loss_ratio(df):
    """ 计算盈亏比 """
    average_win = df[df['pnl'] > 0]['pnl'].mean()
    average_loss = df[df['pnl'] < 0]['pnl'].mean()
    return abs(average_win / average_loss) if average_loss != 0 else 0

def _calculate_max_drawdown(pnl_series):
    """ 计算最大回撤 """
    cumulative_pnl = pnl_series.cumsum()
    cumulative_max = cumulative_pnl.cummax()
    drawdown = cumulative_max - cumulative_pnl
    return drawdown.max()

def _calculate_annual_return(df, init_balance, total_pnl):
    """ 计算年化收益 """
    start_date = df['open_date'].iloc[0]
    end_date = df['close_date'].iloc[-1]
    days = (end_date - start_date).days
    years = days / DAYS_IN_ONE_YEAR if days > 0 else 1  # 防止除零错误
    final_balance = init_balance + total_pnl
    return (((final_balance / init_balance) / years) - 1) if years != 0 else 0

def _calculate_sharpe_ratio(df, init_balance, risk_free_rate):
    """ 计算夏普比率 """
    daily_returns = df['pnl'] / init_balance
    excess_daily_returns = daily_returns - (risk_free_rate / DAYS_IN_ONE_YEAR)
    return (excess_daily_returns.mean() / excess_daily_returns.std()) * np.sqrt(TRADING_DAYS_IN_ONE_YEAR) if excess_daily_returns.std() != 0 else 0
