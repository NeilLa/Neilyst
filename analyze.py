# 本模块是对策略实盘交易历史的分析工具
# 2014.9.14新添加了因子分析工具factor_analyzer

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from .utils.magic import PNL_THRESHOLD

class Factor_Analyzer():
    def __init__(self, indicators):
        self.indicators = indicators
    
    def plot_factor_vs_return(self, factor_column, future_period=1):
        """
        绘制因子与未来收益的散点图 并最小二乘拟合直线

        params:
        factor_column (str): 因子列名
        future_period (int): 计算未来收益的周期
        """
        data = self.indicators.copy()
        data['future_return'] = data['close'].shift(-future_period) / data['close'] - 1
        clean_data = data.dropna(subset=[factor_column, 'future_return'])
        
        # 绘制散点图并添加拟合直线
        plt.figure(figsize=(10, 6))
        sns.regplot(x=factor_column, y='future_return', data=clean_data,
                    scatter_kws={'alpha': 0.5}, line_kws={'color': 'red'})
        plt.title(f'{factor_column} VS {future_period}')
        plt.xlabel(f'{factor_column} Value')
        plt.ylabel(f'Future Return')
        plt.show()

        # 回归模型详细信息
        X = sm.add_constant(clean_data[factor_column])
        y = clean_data['future_return']
        model = sm.OLS(y, X).fit()
        print(model.summary())
        
    def fit_multi_factor_model(self, factor_columns, future_period=1):
        """
        使用多因子进行线性回归，预测未来收益，并评估模型表现

        params:
        factor_columns (list): 因子列名列表
        future_period (int): 计算未来收益的周期
        """
        data = self.indicators.copy()
        data['future_return'] = data['close'].shift(-future_period) / data['close'] - 1
        clean_data = data.dropna(subset=factor_columns + ['future_return'])

        # 多因子线性回归
        X = sm.add_constant(clean_data[factor_columns])
        y = clean_data['future_return']
        model = sm.OLS(y, X).fit()

        # 回归结果与分析
        print("多因子回归结果：")
        print(model.summary())

        # 绘制预测值与实际值的散点图
        predicted = model.predict(X)
        plt.figure(figsize=(10, 6))
        plt.scatter(predicted, clean_data['future_return'], alpha=0.5)
        plt.plot(predicted, predicted, color='red', linestyle='--', linewidth=2, label='Perfect Prediction')
        plt.title('Predicted vs Actual Future Return')
        plt.xlabel('Predicted Future Return')
        plt.ylabel('Actual Future Return')
        plt.grid(True)
        plt.legend()
        plt.show()

        # 返回模型和数据
        return model, clean_data

def load_history(path):
    # 加载账单数据
    history = pd.read_csv(path)
    history['时间'] = pd.to_datetime(history['时间'])
    return history

def calculate_profit_loss_ratio(df, periods=None, symbol=None):
    """
      对外的盈亏比计算接口, 统计交易账单中的盈亏比
    """
    df = _filter_close_order(df)



def calculate_trade_counts(df, periods=None, symbol=None):
    pass

def calculate_win_rate(df, periods=None, symbol=None):
    """
      对外的计算胜率接口, 统计交易账单中的胜率
    
    Parameters
    ------
      periods: list
        起止时间列表, list中每个元素都是一个tuple, 每个tuple中包括了起止时间
        如果这个参数为None, 则计算全时间内的胜率
      symbol: string
        需要计算胜率的标的, 如果这个参数为None, 则计算全币种的胜率, 以及每种交易对的胜率
    """
    df = _filter_close_order(df)

    if periods and symbol:
        return _calculate_win_rate_over_periods(df, periods, symbol)
    
    elif periods:
        return _calculate_win_rate_overall_symbols(df, periods)
    
    elif symbol:
        return _calculate_win_rate_over_periods(df, [(df['时间'].min(), df['时间'].max())], symbol)
    
    else:
        return _calculate_win_rate_over_periods(df, [(df['时间'].min(), df['时间'].max())])

def _calculate_win_rate_overall_symbols(df, periods):
    symbol_win_rate = {}
    symbols = df['产品名称'].unique()

    overall_win_rate = _calculate_win_rate_over_periods(df, periods)

    for sym in symbols:
        sym_win_rate = _calculate_win_rate_over_periods(df, periods, sym)
        symbol_win_rate[sym] = sym_win_rate
    
    sym_win_rate['overall'] = overall_win_rate
    
    return sym_win_rate

def _calculate_win_rate_over_periods(df, periods, symbol=None):
    totals_wins = 0
    totals_trades = 0

    for start, end in periods:
        periods_df = _filter_by_date(df, start, end)
        if symbol:
            periods_df = _filter_by_symbol(periods_df, symbol)
        
        wins = len(periods_df[periods_df['收益'] > 0])
        totals_wins += wins
        totals_trades += len(periods_df)

    overall_win_rate = totals_wins / totals_trades if totals_trades > 0 else 0
    return overall_win_rate

def _calculate_profit_loss_ratio(df, periods, symbol=None):
    pass

def _filter_by_date(df, start, end):
    mask = (df['时间'] >= start) & (df['时间'] < end)
    return df.loc[mask]

def _filter_by_symbol(df, symbol):
    mask = (df['产品名称'] == symbol)
    return df.loc[mask]

def _filter_close_order(df):
    # 过滤掉非平仓数据
    # 账单中开仓的收益为小数点后八个零, 但不为0
    # 所以需要这样过滤
    mask = abs(df['收益']) > PNL_THRESHOLD
    return df.loc[mask]