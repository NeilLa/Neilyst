from .data import get_klines

def backtest(symbol, start, end, strategy):
    # 本函数是对外的回测接口函数
    # 通过接受symbol寻找文件夹中是否有1min级别数据
    # 用此数据来模拟ticker数据进行回测
    # start, end是回测的起止时间
    # strategy是标准的策略对象

    # strategy应该是一个对象
    # 初始金额，手续费，滑点模拟比率由构造函数初始化

    # 回测引擎应该维护一个历史仓位账单，包括每次开平仓价格，确定盈亏，仓位数量，开仓方向
    # 还应该维护一个当前仓位，保存开仓价，方向，数量，浮盈等等

    # 这是针对单个币种进行择时，若是对多币种进行回测
    # 多币种回测目前有两种情况一种是多个币运行同一个策略。这种情况主要重点在统计结果
    # 另一种是同一个策略里包含多个币种，这样传入的symbol似乎是一个list
    # 可以考虑使用一个新的内部函数作为这种情况的驱动引擎

    # 获取1min数据
    ticker_data = get_klines(symbol, start, end, '1m')
    print(ticker_data)
    return

def single_symbol_engine():
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
    def run(self):
        pass