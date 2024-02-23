# 可视化模块
import pandas as pd
import matplotlib.pyplot as plt
def show_pnl(data, indicators, result, init_balance):
    df = pd.DataFrame(data)
    df_result = pd.DataFrame(result)

    # 计算余额变化
    df_result['cumulative_pnl'] = df_result['pnl'].cumsum() + init_balance

    # 设置图像属性
    fig, ax1 = plt.subplot(figsize=(15, 8))

    # 价格曲线
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price', color=color)
    ax1.plot(df['date'], df['close'], color=color, label='Price')
    ax1.tick_params(axis='y', labelcolor=color)

    # 开平仓标记
    for _, row in df_result.iterrows():
        if row['position'] == 'long':
            ax1.plot(row['open_date'], row['open_price'], '^', markersize=10, color='green', label='Long Open')
            ax1.plot(row['close_date'], row['close_price'], 'v', markersize=10, color='red', label='Long Close')
        elif row['position'] == 'short':
            ax1.plot(row['open_date'], row['open_price'], '^', markersize=10, color='red', label='Short Open')
            ax1.plot(row['close_date'], row['close_price'], 'v', markersize=10, color='green', label='Short Close')

    # 画余额变化曲线
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Balance', color=color)
    ax2.plot(df_result['close_date'], df_result['cumulative_pnl'], color=color, label='Balance')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # 画指标曲线
    for indicator_name, indicator_values in indicators.items():
        ax1.plot(df['date'], indicator_values, label=indicator_name)
    
    # 图例
    fig.tight_layout()
    fig.legend(loc="upper left", bbox_to_anchor=(0.05,0.95))
    
    plt.show()