# 本文件用于定义一些通用类
from abc import ABC
from pandas import Timestamp
import pandas as pd

class Strategy(ABC):
    def __init__(self, total_balance, trading_fee_ratio, slippage_ratio, data=None, indicators=None):
        self.total_balance = total_balance
        self.trading_fee_ratio = trading_fee_ratio
        self.slippage_ratio = slippage_ratio
        self.data = data
        self.indicators = indicators

    def get_recent_data(self, date, periods, data=None, indicators=None, symbol=None):
        """
        获取最近的 N 条数据和指标。
        如果传入的 data 和 indicators 是 dict则按 symbol 处理；
        如果传入的是 DataFrame则直接处理。
        """
        if not isinstance(date, Timestamp):
            date = Timestamp(date)

        # 如果传入的数据是 dict，按照 symbol 获取数据
        if isinstance(data, dict) and isinstance(indicators, dict):
            if symbol is None:
                raise ValueError("Symbol must be provided for multi-symbol data.")
            
            # 获取指定 symbol 的数据和指标
            data = self.data[symbol] if data is None else data[symbol]
            indicators = self.indicators[symbol] if indicators is None else indicators[symbol]
        else:
            # 如果不是 dict，直接使用传入的 DataFrame
            data = self.data if data is None else data
            indicators = self.indicators if indicators is None else indicators

        # 找到最近的 N 条数据的位置
        recent_data_idx = data.index[data.index <= date][-periods:]
        recent_indicators_idx = indicators.index[indicators.index <= date][-periods:]

        # 获取最近的 N 条数据和指标
        recent_data = data.loc[recent_data_idx]
        recent_indicators = indicators.loc[recent_indicators_idx]

        # 移除重复的close列
        if 'close' in recent_indicators.columns:
            recent_indicators = recent_indicators.drop(columns=['close'])

        # 合并数据和指标
        recent_combined = pd.concat([recent_data, recent_indicators], axis=1, join='inner')

        return recent_combined

    def run(self, date, price_row, current_pos, current_balance, symbol):
        # run方法每次接收一行1min级别数据用作驱动
        # 以及当前仓位信息, 应该包含开仓价，仓位多少，浮盈浮亏
        # 其余所需数据可以有自己去get_kline以及计算
        # 返回一个对象
        # 对象应该包含开仓方向(long, short, close)
        # 还应该包含开仓价（这个价格自己根据传入的close计算），以及开仓量
        # 如果返回None，则不做任何操作
        pass

class Signal():
    def __init__(self, dir, price, amount):
        self.dir = dir # long/short/None
        self.price = price
        self.amount = amount

class Position():
    def __init__(self, symbol):
        self.symbol = symbol
        self.open_price = 0 # 开仓价
        self.close_price = 0 # 平仓价
        self.dir = None # long/short/None
        self.amount = 0 # 仓位数量
        self.pnl = 0 # 确定盈亏
        self.float_profit = 0 # 浮动盈亏
        self.open_date = None
        self.close_date = None
        self.trade_cost = 0 # 手续费和滑点

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
        # 先检查是否有足够的仓位可供平仓
        if amount > self.amount:
            print("Error: Attempting to close more than the available position")
            return
        
        # 计算确定盈亏
        if self.dir == 'long':
            self.pnl += (current_price - self.open_price) * amount
        elif self.dir == 'short':
            self.pnl += (self.open_price - current_price) * amount
        
        self.amount -= amount

        # 如果当前仓位为0，则确认完全平仓
        if self.amount == 0:
            self.close_date = current_date
            self.close_price = current_price