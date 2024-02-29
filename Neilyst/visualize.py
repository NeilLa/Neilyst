# 可视化模块
import pandas as pd
import matplotlib.pyplot as plt
def show_pnl(data, indicators, result, init_balance):
    df = pd.DataFrame(data)
    df_result = pd.DataFrame(result)

    # 计算余额变化
    df_result['cumulative_pnl'] = df_result['pnl'].cumsum() + init_balance

    # 设置图像属性
    fig, ax1 = plt.subplots(figsize=(15, 8))

    # 价格曲线
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price', color=color)
    ax1.plot(df.index, df['close'], color=color, label='Price')
    ax1.tick_params(axis='y', labelcolor=color)

    # 已添加图例的标记
    legend_added = {"long_open": False, "long_close": False, "short_open": False, "short_close": False}

    # 开平仓标记
    for _, row in df_result.iterrows():
        if row['dir'] == 'long':
            if not legend_added["long_open"]:
                ax1.plot(row['open_date'], row['open_price'], '^', markersize=10, color='green', label='Long Open')
                legend_added["long_open"] = True
            else:
                ax1.plot(row['open_date'], row['open_price'], '^', markersize=10, color='green', label="_nolegend_")

            if not legend_added["long_close"]:
                ax1.plot(row['close_date'], row['close_price'], 'v', markersize=10, color='red', label='Long Close')
                legend_added["long_close"] = True
            else:
                ax1.plot(row['close_date'], row['close_price'], 'v', markersize=10, color='red', label="_nolegend_")
        elif row['dir'] == 'short':
            if not legend_added["short_open"]:
                ax1.plot(row['open_date'], row['open_price'], '^', markersize=10, color='red', label='Short Open')
                legend_added["short_open"] = True
            else:
                ax1.plot(row['open_date'], row['open_price'], '^', markersize=10, color='red', label="_nolegend_")

            if not legend_added["short_close"]:
                ax1.plot(row['close_date'], row['close_price'], 'v', markersize=10, color='green', label='Short Close')
                legend_added["short_close"] = True
            else:
                ax1.plot(row['close_date'], row['close_price'], 'v', markersize=10, color='green', label="_nolegend_")

    # 画余额变化曲线
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Balance', color=color)
    ax2.plot(df_result['close_date'], df_result['cumulative_pnl'], color=color, label='Balance')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # 画指标曲线
    for indicator_name, indicator_values in indicators.items():
        ax1.plot(df.index, indicator_values, label=indicator_name)
    
    # 图例
    ax1.legend()
    fig.tight_layout()
    
    plt.show()