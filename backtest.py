import pandas as pd
import numpy as np
from tqdm import tqdm
import datetime
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

def cross_sectional_backtest(universe_data, symbol_selector, signal_generator, start, end):
    """
    截面策略回测引擎
    输入全币种数据->symbol_selector
    返回一个dict, key为选出的一个symbol, value是一个具体的值, 可以是系数, 权重等等

    这个dict输入signal_generator, 这个函数应该自动提取这些币的数据, 然后进行回测
    最终返回一个交易信号

    回测完成后, 整理统计交易信号
    并生成result
    """
    pass

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
            # 开仓逻辑
            if signal.dir == 'long' or signal.dir == 'short':
                # 计算开仓时的交易费用
                open_cost = signal.amount * signal.price
                trade_cost = open_cost * (trading_fee_ratio + slippage_ratio)
                # 执行开仓操作
                current_pos.open(signal.price, signal.amount, signal.dir, index)
                current_pos.trade_cost = trade_cost  # 记录开仓时的交易费用
                if signal.dir == 'long':
                    # 更新余额
                    current_balance -= open_cost + trade_cost
                elif signal.dir == 'short':
                    # 更新余额，只扣除交易费用（假设无需保证金）
                    current_balance -= trade_cost
            elif signal.dir == 'close':
                close_amount = min(signal.amount, current_pos.amount)
                if close_amount > 0:
                    if current_pos.dir == 'long':
                        # 计算卖出所得
                        proceeds = close_amount * signal.price
                        trade_cost = proceeds * (trading_fee_ratio + slippage_ratio)
                        net_proceeds = proceeds - trade_cost
                        # 更新余额
                        current_balance += net_proceeds
                        # 计算净利润
                        profit = net_proceeds - (current_pos.open_price * close_amount + current_pos.trade_cost)
                        # 记录平仓交易费用
                        current_pos.close_trade_cost = trade_cost
                    elif current_pos.dir == 'short':
                        # 计算买入成本
                        cost = close_amount * signal.price
                        trade_cost = cost * (trading_fee_ratio + slippage_ratio)
                        net_cost = cost + trade_cost
                        # 计算净利润
                        profit = (current_pos.open_price * close_amount - net_cost) - current_pos.trade_cost
                        # 更新余额
                        current_balance += profit
                        # 记录平仓交易费用
                        current_pos.close_trade_cost = trade_cost
                    # 执行平仓
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
                            'amount': current_pos.amount,
                            'pnl': profit,
                            'open_fee': current_pos.trade_cost,
                            'close_fee': current_pos.close_trade_cost,
                            'balance': current_balance
                        })

                        # 重新初始化pos对象
                        current_pos = Position(symbol)

    # 整体回测结束，平掉所有仓位
    if current_pos.amount > 0:
        final_price = ticker_data.iloc[-1]['close']
        if current_pos.dir == 'long':
            # 计算卖出所得
            proceeds = current_pos.amount * final_price
            trade_cost = proceeds * (trading_fee_ratio + slippage_ratio)
            net_proceeds = proceeds - trade_cost
            # 更新余额
            current_balance += net_proceeds
            # 计算净利润
            profit = net_proceeds - (current_pos.open_price * current_pos.amount + current_pos.trade_cost)
            # 记录平仓交易费用
            current_pos.close_trade_cost = trade_cost
        elif current_pos.dir == 'short':
            # 计算买入成本
            cost = current_pos.amount * final_price
            trade_cost = cost * (trading_fee_ratio + slippage_ratio)
            net_cost = cost + trade_cost
            # 计算净利润
            profit = (current_pos.open_price * current_pos.amount - net_cost) - current_pos.trade_cost
            # 更新余额
            current_balance += profit
            # 记录平仓交易费用
            current_pos.close_trade_cost = trade_cost
        
        # 记录最后仓位
        pos_history.append({
            'open_date': current_pos.open_date,
            'close_date': ticker_data.index[-1],
            'dir': current_pos.dir,
            'open_price': current_pos.open_price,
            'close_price': final_price,
            'amount': current_pos.amount,
            'pnl': profit,
            'open_fee': current_pos.trade_cost,
            'close_fee': current_pos.close_trade_cost,
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
    if isinstance(result, list):
        # 单 symbol 情况，直接调用单 symbol 评估函数
        return _evaluate_single_symbol(result, init_balance, risk_free_rate)
    elif isinstance(result, dict):
        # 多 symbol 情况，基于组合净值曲线计算综合指标
        return _evaluate_multi_symbol(result, init_balance, risk_free_rate)
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
    
    #平均持仓时长（按小时计）
    df['holding_time'] = (df['close_date'] - df['open_date']).dt.total_seconds() / 3600  # 转换为小时
    average_holding_time = df['holding_time'].mean()

    #最大持仓时间
    max_holding_time = df['holding_time'].max()

    #单次最大盈利（盈利数额，发生时间）
    max_profit_trade = df.loc[df['pnl'].idxmax()]
    max_profit = max_profit_trade['pnl']
    max_profit_time = max_profit_trade['close_date']

    #单次最大亏损（亏损数额，发生时间）
    max_loss_trade = df.loc[df['pnl'].idxmin()]
    max_loss = max_loss_trade['pnl']
    max_loss_time = max_loss_trade['close_date']

    return {
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'profit_loss_ratio': profit_loss_ratio,
        'max_drawdown': max_drawdown,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'total_trades': total_trades,
        'average_daily_trades': average_daily_trades,
        'average_holding_time_hours': average_holding_time,
        'max_holding_time_hours': max_holding_time,
        'max_profit': max_profit,
        'max_profit_time': max_profit_time,
        'max_loss': max_loss,
        'max_loss_time': max_loss_time,
        'start_date': start_date,
        'end_date': end_date
    }

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
    """
    计算简单年化收益率（不考虑复利）。
    
    参数：
    - df: 包含交易记录的DataFrame，必须包含'open_date'和'close_date'列，且为datetime类型。
    - init_balance: 初始资金（正数）。
    - total_pnl: 总盈亏（可以为负数）。
    
    返回：
    - annual_return: 简单年化收益率（浮点数）。
    """
    # 检查初始资金
    if init_balance <= 0:
        raise ValueError("初始资金必须为正数")
    
    # 检查交易记录
    if df.empty:
        return 0

    # 确保日期列为datetime类型
    df['open_date'] = pd.to_datetime(df['open_date'])
    df['close_date'] = pd.to_datetime(df['close_date'])
    
    start_date = df['open_date'].iloc[0]
    end_date = df['close_date'].iloc[-1]
    total_days = (end_date - start_date).days
    
    if total_days <= 0:
        return 0  # 交易周期不足，无法计算年化收益
    
    years = total_days / DAYS_IN_ONE_YEAR

    # 计算简单年化收益率
    annual_return = (total_pnl) / (init_balance * years)
    return annual_return

def _calculate_sharpe_ratio(df, init_balance, risk_free_rate):
    """ 计算夏普比率 """
    daily_returns = df['pnl'] / init_balance
    excess_daily_returns = daily_returns - (risk_free_rate / DAYS_IN_ONE_YEAR)
    return (excess_daily_returns.mean() / excess_daily_returns.std()) * np.sqrt(TRADING_DAYS_IN_ONE_YEAR) if excess_daily_returns.std() != 0 else 0

def _evaluate_multi_symbol(results, init_balance, risk_free_rate):
    """
    评估多 symbol 策略的绩效指标。

    参数:
    - results: 多 symbol 的交易结果字典，键为 symbol，值为交易结果列表。
    - init_balance: 初始资金。
    - risk_free_rate: 无风险利率。

    返回:
    - 一个包含总收益、胜率、盈亏比、最大回撤、年化收益率、夏普比率等指标的字典。
    """

    # 构建组合的净值时间序列
    all_balances = pd.DataFrame()

    # 用于计算整体的交易记录
    all_trades = []

    for symbol, trades in results.items():
        df_trades = pd.DataFrame(trades)

        if df_trades.empty:
            print(f'No trading result for {symbol}')
            continue

        # 将该 symbol 的交易记录添加到总的交易记录中
        all_trades.append(df_trades)

        # 提取 'close_date' 和 'balance' 列，构建余额时间序列
        balance_series = df_trades[['close_date', 'balance']].copy()
        balance_series['close_date'] = pd.to_datetime(balance_series['close_date'])
        balance_series.set_index('close_date', inplace=True)

        # 添加初始余额点
        earliest_date = balance_series.index.min()
        initial_balance_df = pd.DataFrame({
            'balance': [init_balance]
        }, index=[earliest_date])

        balance_series = pd.concat([initial_balance_df, balance_series], axis=0)
        balance_series = balance_series.sort_index()
        balance_series = balance_series[~balance_series.index.duplicated(keep='first')]

        # 将该 symbol 的余额时间序列添加到 all_balances DataFrame 中
        balance_series = balance_series.rename(columns={'balance': symbol})
        all_balances = pd.concat([all_balances, balance_series], axis=1)

    if all_balances.empty:
        print('No trading data available.')
        return

    # 对齐所有 symbol 的日期索引
    all_balances = all_balances.sort_index()
    # 使用前向填充填充缺失值
    all_balances = all_balances.fillna(method='ffill')
    # 将初始缺失值填充为初始余额
    all_balances = all_balances.fillna(init_balance)

    # 获取所有的 symbol 列
    symbol_columns = [col for col in all_balances.columns if col != 'Total Balance']
    # 计算组合的总余额
    all_balances['Total Balance'] = all_balances[symbol_columns].sum(axis=1)

    # 计算组合的每日收益率
    all_balances['Daily Return'] = all_balances['Total Balance'].pct_change().fillna(0)

    # 计算总盈亏
    total_pnl = all_balances['Total Balance'].iloc[-1] - init_balance

    # 将所有交易记录合并
    if all_trades:
        all_trades_df = pd.concat(all_trades, ignore_index=True)
    else:
        print('No trading records available.')
        return

    # 计算胜率和盈亏比
    win_rate = _calculate_win_rate(all_trades_df)
    profit_loss_ratio = _calculate_profit_loss_ratio(all_trades_df)
    total_trades = len(all_trades_df)

    # 计算年化收益率
    start_date = all_balances.index.min()
    end_date = all_balances.index.max()
    total_days = (end_date - start_date).days

    annual_return = _calculate_annual_return_from_balance(all_balances['Total Balance'], init_balance, total_days)

    # 计算最大回撤
    max_drawdown = _calculate_max_drawdown_from_balance(all_balances['Total Balance'])

    # 计算夏普比率
    sharpe_ratio = _calculate_sharpe_ratio_from_returns(all_balances['Daily Return'], risk_free_rate)

    # 平均每日交易次数
    average_daily_trades = total_trades / total_days if total_days > 0 else 0

    return {
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'profit_loss_ratio': profit_loss_ratio,
        'max_drawdown': max_drawdown,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'total_trades': total_trades,
        'average_daily_trades': average_daily_trades
    }

# 基于组合净值计算年化收益率
def _calculate_annual_return_from_balance(balance_series, init_balance, total_days):
    """
    基于组合的净值序列计算年化收益率。

    参数：
    - balance_series: 组合的净值时间序列。
    - init_balance: 初始资金。
    - total_days: 回测的总天数。

    返回：
    - annual_return: 年化收益率。
    """
    final_balance = balance_series.iloc[-1]
    total_return = final_balance / init_balance
    years = total_days / DAYS_IN_ONE_YEAR
    if years <= 0:
        return 0
    annual_return = total_return ** (1 / years) - 1
    return annual_return

# 基于组合净值计算最大回撤
def _calculate_max_drawdown_from_balance(balance_series):
    """ 计算最大回撤 """
    cumulative_max = balance_series.cummax()
    drawdown = (balance_series - cumulative_max) / cumulative_max
    return drawdown.min()

# 基于组合的每日收益率计算夏普比率
def _calculate_sharpe_ratio_from_returns(daily_returns, risk_free_rate):
    """ 计算夏普比率 """
    excess_daily_returns = daily_returns - (risk_free_rate / DAYS_IN_ONE_YEAR)
    if excess_daily_returns.std() == 0:
        return 0
    sharpe_ratio = (excess_daily_returns.mean() / excess_daily_returns.std()) * np.sqrt(TRADING_DAYS_IN_ONE_YEAR)
    return sharpe_ratio