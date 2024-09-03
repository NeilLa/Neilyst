import pandas as pd
import numpy as np
from tqdm import tqdm
import datetime
import matplotlib.pyplot as plt
from .data import get_klines
from .models import Position
from .utils.magic import US_TREASURY_YIELD, DAYS_IN_ONE_YEAR, TRADING_DAYS_IN_ONE_YEAR, TIMEZONE

def backtest(symbol, start, end, strategy):
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

    # 判断是单币种还是多币种策略

    result = []

    if isinstance(symbol, str):
        # 运行回测引擎得到结果
        result = _single_symbol_engine(symbol, start, end, strategy)
        # 修改回测账单时区
        result = _convert_result_time(result, TIMEZONE)
        
    elif isinstance(symbol, list):
        _multi_symbol_engine(symbol, start, end, strategy)

    return result

def _single_symbol_engine(symbol, start, end, strategy):
    # 获取1min数据
    ticker_data = get_klines(symbol, start, end, '1m')
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
        signal = strategy.run(index, row, current_pos, current_balance)

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

def _multi_symbol_engine(symbols, start, end, strategy):
    pos_historys = dict()
    for symbol in symbols:
        pos_historys[symbol] = _single_symbol_engine(symbol, start, end, strategy)
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
    df = pd.DataFrame(result)

    if df.empty:
        print('No trading result')
        return
    
    # 总盈亏
    total_pnl = df['pnl'].sum()

    # 胜率
    win_rate = (df['pnl'] > 0).mean()

    # 盈亏比
    profit_loss_ratio = 0
    average_win = df[df['pnl'] > 0]['pnl'].mean()
    average_loss = df[df['pnl'] < 0]['pnl'].mean()
    if average_loss != 0:
        profit_loss_ratio = abs(average_win / average_loss)

    # 最大回撤
    cumulative_pnl = df['pnl'].cumsum()
    cumulative_max = cumulative_pnl.cummax()
    drawdown = cumulative_max - cumulative_pnl
    max_drawdown = drawdown.max()
    
    # 年化收益
    start_date = df['open_date'].iloc[0]
    end_date = df['close_date'].iloc[-1]
    days = (end_date - start_date).days
    years = days / DAYS_IN_ONE_YEAR
    final_balance = init_balance + total_pnl
    annual_return = (((final_balance / init_balance) / years) - 1) if years != 0 else 0

    # 夏普比率
    daliy_returns = df['pnl'] / init_balance
    excess_daily_returns = daliy_returns - (risk_free_rate / DAYS_IN_ONE_YEAR)
    sharpe_ratio = (excess_daily_returns.mean() / excess_daily_returns.std()) * np.sqrt(TRADING_DAYS_IN_ONE_YEAR) if excess_daily_returns.std() != 0 else 0
    
    print(f'总收益: {total_pnl}')
    print(f'总胜率: {win_rate}')
    print(f'盈亏比: {profit_loss_ratio}')
    print(f'最大回撤: {max_drawdown}')
    print(f'年化收益率: {annual_return * 100}%')
    print(f'夏普比率: {sharpe_ratio}')

    return {
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'profit_loss_ratio': profit_loss_ratio,
        'max_drawdown': max_drawdown,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio
    }

def analyze_multi_symbol_results(pos_historys, init_balance, risk_free_rate=US_TREASURY_YIELD):
    # 初始化总统计数据
    cumulative_pnl = pd.Series(dtype='float64')
    
    # 创建绘图
    plt.figure(figsize=(14, 7))

    for symbol, history in pos_historys.items():
        if not history:
            print(f'No trading result for {symbol}')
            continue

        # 计算累计 PnL
        df = pd.DataFrame(history)
        symbol_cumulative_pnl = df['pnl'].cumsum()
        cumulative_pnl = cumulative_pnl.add(symbol_cumulative_pnl, fill_value=0)
        
        # 绘制每个 symbol 的 PnL 曲线
        plt.plot(symbol_cumulative_pnl.index, symbol_cumulative_pnl, label=symbol)

    # 使用 evaluate_strategy 函数计算所有 symbol 的总指标
    total_stats = evaluate_strategy(cumulative_pnl.reset_index().to_dict('records'), init_balance, risk_free_rate)

    print(f'总收益: {total_stats["total_pnl"]}')
    print(f'总胜率: {total_stats["win_rate"]}')
    print(f'盈亏比: {total_stats["profit_loss_ratio"]}')
    print(f'最大回撤: {total_stats["max_drawdown"]}')
    print(f'年化收益率: {total_stats["annual_return"] * 100}%')
    print(f'夏普比率: {total_stats["sharpe_ratio"]}')

    return total_stats