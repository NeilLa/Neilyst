from .data import get_klines
from .models import Position

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
        result = _single_symbol_engine(symbol, start, end, strategy)
    elif isinstance(symbol, list):
        _multi_symbol_engine()

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

    for index, row in ticker_data.iterrows():
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
                current_balance -= trade_cost
            elif signal.dir == 'close':
                close_amount = min(signal.amount, current_pos.amount)
                if close_amount > 0:
                    trade_cost = close_amount * signal.price * (trading_fee_ratio + slippage_ratio)
                    if current_pos == 'long':
                        current_balance += close_amount * signal.price - trade_cost
                    elif current_pos == 'short':
                        current_balance += (current_pos.open_price - signal.price) * close_amount - trade_cost
                    
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
                        'amount': current_pos.pnl / abs(current_pos.open_price - current_pos.close_price),
                        'pnl': current_pos.pnl,
                        'balance': current_balance
                    })

                    # 重新初始化pos对象
                    current_pos = Position(symbol)

    return pos_history

def _multi_symbol_engine():
    pass

