from Analytics import Indicators
import pandas as pd

class Strategy(Indicators):
    def __init__(self, exchange_name) -> None:
        super().__init__(exchange_name)

    def __get_data(self) -> None:
        self.data = pd.concat([self.ohlcv_data, self.indicators], axis=1)

    def run_backtest(self, strategy) -> None:
        # 拼接数据
        self.__get_data()
        
        # 初始化交易记录
        self.trade_record = pd.DataFrame(columns=['signal', 'price', 'amount', 'pnl'])

        # 设置初始值
        self.data['pos'] = 0
        self.data['balance'] = 0
        self.data['total'] = 0
        self.data['entry_price'] = 0
        
        self.balance = self.init_amount
        self.total = self.init_amount
        self.pos = 0
        self.entry_price = 0

        # 运行回测
        for index, row in self.data.iterrows():
            signal = strategy.check_signal(index, row)
            if signal:
                self.trade(signal, index,row)

    def trade(self, signal, index, row) -> None:
        # 假设当前价格即为close价格
        price = row['close']
        
        # 开多仓
        if signal == 'long':
            # 价格处理
            long_price = price * (1 + self.slippage_rate) #考虑滑点
            fee = self.balance * self.fee_rate
            amount_to_invest = self.balance - fee  # 扣除手续费后的金额
            long_amount = amount_to_invest / long_price  # 购买的数量

            # 更新全局数据
            self.balance = 0
            self.total = self.balance + long_amount * long_price
            self.pos += long_amount
            self.entry_price = long_price
            
            # 更新大表数据
            self.data.at[index, 'pos'] += long_amount
            self.data.at[index, 'balance'] = self.balance 
            self.data.at[index, 'total'] = self.total
            self.data.at[index, 'entry_price'] = long_price
            
            # 更新交易记录
            self.trade_record.loc[index] = [signal,long_price, long_amount, 0]

        # 开空仓
        elif signal == 'short':
            # 价格处理
            short_price = price * (1 - self.slippage_rate) #考虑滑点
            fee = self.balance * self.fee_rate
            amount_to_invest = self.balance - fee  # 扣除手续费后的金额
            short_amount = amount_to_invest / short_price  # 借入并卖出的数量

            # 更新全局数据
            self.balance += amount_to_invest
            self.total = self.balance - short_amount * short_price - fee
            self.pos -= short_amount
            self.entry_price = short_price

            # 更新大表数据
            self.data.at[index, 'pos'] -= short_amount
            self.data.at[index, 'balance'] = self.balance 
            self.data.at[index, 'total'] = self.total
            self.data.at[index, 'entry_price'] = short_price

            # 更新交易记录
            self.trade_record.loc[index] = [signal,short_price, short_amount, 0]
        
        # 平仓
        elif signal == 'close' or 'take_profit' or 'stop_loss':
            # 平多仓， 以当前价格卖出
            if self.pos > 0:
                # 价格处理
                sell_price = price * (1 - self.slippage_rate)
                amount = self.pos
                fee = self.pos * sell_price * self.fee_rate
                pnl = (sell_price - self.entry_price) * self.pos

                # 更新全局
                self.balance += self.pos * sell_price - fee
                self.total = self.balance
                self.pos = 0

                # 更新大表
                self.data.at[index, 'pos'] = self.pos
                self.data.at[index, 'balance'] = self.balance
                self.data.at[index, 'total'] = self.total
                self.data.at[index, 'entry_price'] = self.entry_price

                # 更新交易记录
                self.trade_record.loc[index] = [signal, sell_price, amount, pnl]
            
            if self.pos < 0:
                # 价格处理
                buy_price = price * (1 + self.slippage_rate)
                amount = self.pos
                fee = abs(self.pos) * buy_price * self.fee_rate
                pnl = (buy_price - self.entry_price) * self.pos

                # 更新全局
                self.balance += self.pos * buy_price - fee
                self.total = self.balance
                self.pos = 0
        
                # 更新大表
                self.data.at[index, 'pos'] = self.pos
                self.data.at[index, 'balance'] = self.balance
                self.data.at[index, 'total'] = self.total
                self.data.at[index, 'entry_price'] = self.entry_price

                # 更新交易记录
                self.trade_record.loc[index] = [signal, buy_price, amount, pnl]


class myStrategy():
    def check_signal(self, index, row):
        pass

    
if __name__ == "__main__":
    btc = Strategy('binanceusdm')
    btc.fetch('BTC/USDT', '2022-01-01T00:00:00Z', '2022-02-01T00:00:00Z', timeframe='1d')

    btc.MA(20)
    btc.MA(60)

    btc.run_backtest('test')
    print(btc.data.head())
    print(btc.trade_record)
