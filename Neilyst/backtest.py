from .data import get_klines

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
    if isinstance(symbol, str):
        _single_symbol_engine(symbol, start, end, strategy)
    elif isinstance(symbol, list):
        _muti_symbol_engine()

    return

def _single_symbol_engine(symbol, start, end, strategy):
    # 获取1min数据
    ticker_data = get_klines(symbol, start, end, '1m')

    # 初始化仓位历史记录
    current_pos = position()
    pos_history = []

    for index, row in ticker_data.iterrows():
        
        # 从策略函数获取策略信号
        signal = strategy.run(index, row, current_pos)

        if signal != None:
            pass

    return pos_history

def _muti_symbol_engine():
    pass

class strategy():
    def __init__(self, total_balance, trading_fee_ratio, slippage_ratio):
        self.total_balance = total_balance
        self.trading_fee_ratio = trading_fee_ratio
        self.slippage_ratio = slippage_ratio

    # run方法每次接收一行1min级别数据用作驱动
    # 以及当前仓位信息, 应该包含开仓价，仓位多少，浮盈浮亏
    # 其余所需数据可以有自己去get_kline以及计算
    # 返回一个对象
    # 对象应该包含开仓方向(long, short, close)
    # 还应该包含开仓价（这个价格自己根据传入的close计算），以及开仓量
    # 如果返回0，则不做任何操作
    def run(self, date, price_row, current_pos):
        # 初始化返回信号
        signal = dict()
        signal['dir'] = None
        signal['price'] = 0
        signal['amount'] = 0
        pass

class position():
    def __init__(self):
        self.open_price = 0 # 开仓价
        self.close_price = 0 # 平仓价
        self.dir = None # long/short/None
        self.amount = 0 # 仓位数量
        self.pnl = 0 # 确定盈亏
        self.float_profit = 0 # 浮动盈亏
        self.open_date = None
        self.close_date = None

    def update_float_profit(self, current_price):
        # 根据当前价格更新浮动盈亏
        if self.dir == 'long':
            self.float_profit = (current_price - self.open_price) * self.amount
        elif self.dir == 'short':
            self.float_profit = (self.open_price - current_price) * self.amount
        else:
            self.float_profit = 0

    def open(self, current_price, amount, dir, current_date):
        # 如果当前有仓位
        if self.amount > 0 and self.dir == dir:
            total_cost = self.open_price * self.amount
            additional_cost = current_price * amount

            current_total_amount = self.amount + amount
            
            # 根据加权平均计算开仓价
            self.open_price = (total_cost + additional_cost) / current_total_amount

            self.amount = current_total_amount
        else:
            # 当前没有仓位
            self.open_price = current_price
            self.amount = amount
            self.dir = dir
        
        self.open_date = current_date

    def close(self, current_price, amount, current_date):
        pass