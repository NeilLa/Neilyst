from Analytics import Indicators
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
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
        self.trade_record = pd.DataFrame(columns=['date', 'signal', 'price', 'amount', 'pnl'])

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
            signal = strategy.check_signal(index, row, self.data, self.pos)
            if signal:
                self.trade(signal, index, row)
            else:
                # 如果没有信号，则更新大表数据即可
                self.data.at[index, 'pos'] += self.pos
                self.data.at[index, 'balance'] = self.balance 
                self.data.at[index, 'total'] = self.balance + self.pos * self.data.at[index, 'close']
                self.data.at[index, 'entry_price'] = self.entry_price

    def trade(self, signals, index, row) -> None:
        # 假设当前价格即为close价格
        price = row['close']
        
        for signal in signals:
            if signal == 'long' or signal == 'short':
                self.open_position(signal, index, price)
            if signal == 'close' or signal == 'take_profit' or signal == 'stop_loss':
                self.close_position(signal, index, price)

    def open_position(self, signal, index, price) -> None:
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
            record = pd.DataFrame([[index, signal, long_price, long_amount, 0]], columns=['date', 'signal', 'price', 'amount', 'pnl'])
            self.trade_record = pd.concat([self.trade_record, record])

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
            record = pd.DataFrame([[index, signal, short_price, short_amount, 0]], columns=['date', 'signal', 'price', 'amount', 'pnl'])
            self.trade_record = pd.concat([self.trade_record, record])

    def close_position(self, signal, index, price) -> None:
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
            self.entry_price = 0

            # 更新大表
            self.data.at[index, 'pos'] = self.pos
            self.data.at[index, 'balance'] = self.balance
            self.data.at[index, 'total'] = self.total
            self.data.at[index, 'entry_price'] = self.entry_price

            # 更新交易记录
            record = pd.DataFrame([[index, signal, sell_price, amount, pnl]], columns=['date', 'signal', 'price', 'amount', 'pnl'])
            self.trade_record = pd.concat([self.trade_record, record])
        
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
            self.entry_price = 0
    
            # 更新大表
            self.data.at[index, 'pos'] = self.pos
            self.data.at[index, 'balance'] = self.balance
            self.data.at[index, 'total'] = self.total
            self.data.at[index, 'entry_price'] = self.entry_price

            # 更新交易记录
            record = pd.DataFrame([[index, signal, buy_price, amount, pnl]], columns=['date', 'signal', 'price', 'amount', 'pnl'])
            self.trade_record = pd.concat([self.trade_record, record])

    def evaluate(self) -> None:
        if self.trade_record.empty:
            print("No trade records.")
            return

        # 计算胜率
        wins = self.trade_record[self.trade_record['pnl'] > 0]
        all_close = self.trade_record[self.trade_record['signal'] == 'close']
        all_take_profit = self.trade_record[self.trade_record['signal'] == 'take_profit']
        all_stop_loss = self.trade_record[self.trade_record['signal'] == 'stop_loss']
        win_rate = len(wins) / (len(all_close) + len(all_take_profit) + len(all_stop_loss))  
        
        # 计算盈亏比
        average_win = wins['pnl'].mean() if len(wins) > 0 else 0
        losses = self.trade_record[self.trade_record['pnl'] < 0]
        average_loss = losses['pnl'].mean() if len(losses) > 0 else 0
        profit_loss_ratio = -average_win/average_loss if average_loss != 0 else 0

        # 计算最大回撤
        running_capital = self.data['total'].cummax()
        drawdown = (running_capital - self.data['total']) / running_capital
        max_drawdown = drawdown.max()

        # 计算收益率
        final_return = self.data['total'].iloc[-1] / self.data['total'].iloc[0] - 1

        # 打印结果
        print(f"胜率: {win_rate:.2f}")
        print(f"盈亏比: {profit_loss_ratio:.2f}")
        print(f"最大回撤: {max_drawdown:.2f}")
        print(f"收益率: {final_return:.2f}")
    
    def show_pnl(self) -> None:
        # 设定绘图风格
        plt.style.use('seaborn-darkgrid')

        # 创建图形和轴
        fig, ax1 = plt.subplots(figsize=(14, 7))

        # 绘制价格曲线
        for i in range(1, len(self.data)):
            if self.data['pos'][i] > 0:  # 持有多头仓位
                ax1.plot(self.data.index[i-1:i+1], self.data['close'][i-1:i+1], color='green')
            elif self.data['pos'][i] < 0:  # 持有空头仓位
                ax1.plot(self.data.index[i-1:i+1], self.data['close'][i-1:i+1], color='red')
            else:  # 无仓位
                ax1.plot(self.data.index[i-1:i+1], self.data['close'][i-1:i+1], color='gray')

        # 添加总资产曲线
        ax2 = ax1.twinx()
        ax2.plot(self.data.index, self.data['total'], color='blue', linestyle='--')

        # 设置轴标签和图例
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Close Price', color='black')
        ax2.set_ylabel('Total Value', color='blue')
        ax1.tick_params(axis='y', labelcolor='black')
        ax2.tick_params(axis='y', labelcolor='blue')
        ax1.legend(['Close Price'], loc='upper left')
        ax2.legend(['Total Value'], loc='upper right')

        # 设置x轴日期格式
        # 设置x轴日期格式
        date_form = DateFormatter("%m-%d")
        ax1.xaxis.set_major_formatter(date_form)

        # 显示图形
        plt.title('Close Price with Trading Position and Total Value Over Time')
        plt.show()

