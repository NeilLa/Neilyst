from .data import get_klines

def backtest(symbol, start, end, strategy):
    # 本函数是对外的回测接口函数
    # 通过接受symbol寻找文件夹中是否有1min级别数据
    # 用此数据来模拟ticker数据进行回测
    # start, end是回测的起止时间
    # strategy是标准的策略对象/函数

    # 获取1min数据
    ticker_data = get_klines(symbol, start, end, '1m')
    print(ticker_data)
    return