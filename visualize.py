# 可视化模块
import pandas as pd
import matplotlib.pyplot as plt

def show_pnl(data, result, init_balance, indicators=None):
    df = pd.DataFrame(data)
    df_result = pd.DataFrame(result)

    if df_result.empty:
        return

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
    if indicators:
        for indicator_name, indicator_values in indicators.items():
            if indicator_name not in ['rsi', 'volumn', 'macd']:
                ax1.plot(df.index, indicator_values, label=indicator_name)
    
    # 图例
    ax1.legend()
    fig.tight_layout()
    
    plt.show()

def show_multi_symbol_pnl(results, init_balance):
    """
    显示多个symbol的PnL曲线，并绘制总的PnL曲线
    """
    plt.figure(figsize=(15, 8))

    cumulative_pnl = pd.Series(dtype='float64')
    symbol_colors = {}  # 存储每个symbol的颜色

    # 遍历每个symbol的回测结果
    for symbol, history in results.items():
        df = pd.DataFrame(history)

        if df.empty:
            print(f'No trading result for {symbol}')
            continue

        # 计算每个symbol的累计PnL
        df['cumulative_pnl'] = df['pnl'].cumsum() + init_balance
        cumulative_pnl = cumulative_pnl.add(df['pnl'].cumsum(), fill_value=0)

        # 为每个symbol分配颜色，并绘制PnL曲线
        color = plt.cm.tab10(len(symbol_colors) % 10)  # 从10种颜色中选择
        symbol_colors[symbol] = color
        plt.plot(df['close_date'], df['cumulative_pnl'], label=f'{symbol} PnL', color=color)

    # 计算并绘制总的PnL曲线
    cumulative_pnl += init_balance
    plt.plot(cumulative_pnl.index, cumulative_pnl, label='Total PnL', linewidth=2, color='black')

    # 图表美化
    plt.title('PnL Curves for Multiple Symbols')
    plt.xlabel('Date')
    plt.ylabel('PnL')
    plt.legend()
    plt.grid(True)

    # 显示图表
    plt.show()

def show_indicators(data, indicators):
    # 确定有多少个指标需要放在副图中
    subplots_needed = sum(1 for indicator_name in indicators if indicator_name in ['rsi', 'volume', 'macd'])

    # 创建足够的子图来容纳所有指标
    # 添加squeeze=False确保axes始终是数组形式
    fig, axes = plt.subplots(subplots_needed + 1, 1, figsize=(15, 8), sharex=True, squeeze=False)
    fig.subplots_adjust(hspace=0)  # 调整子图之间的间距

    # 主图显示价格和可能的一些其他指标
    axes[0,0].plot(data.index, data['close'], label='Price')  # 修改为axes[0,0]访问第一个子图
    
    # 遍历所有指标，决定它们应该放在主图还是副图
    subplot_index = 1  # 副图的索引从1开始
    for indicator_name, indicator_values in indicators.items():
        if indicator_name in ['rsi', 'volume', 'macd']:
            # 放在副图
            ax = axes[subplot_index, 0]  # 修改为axes[subplot_index, 0]
            subplot_index += 1
            if indicator_name == 'volume':
                ax.bar(data.index, indicator_values, label=indicator_name)
            else:
                ax.plot(data.index, indicator_values, label=indicator_name)
            ax.legend(loc='upper left')
        else:
            # 放在主图
            axes[0,0].plot(data.index, indicator_values, label=indicator_name)  # 修改为axes[0,0]

    axes[0,0].legend(loc='upper left')  # 修改为axes[0,0]
    
    # 允许用户放大缩小图表来观察细节
    # 在jupter notebook中会有bug
    # plt.get_current_fig_manager().toolbar.zoom()

    # 显示图表
    plt.show()