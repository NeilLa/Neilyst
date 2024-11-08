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

    # 获取初始日期
    initial_date = df.index[0]

    # 创建包含初始余额的DataFrame
    initial_balance_df = pd.DataFrame({
        'close_date': [initial_date],
        'cumulative_pnl': [init_balance]
    })

    # 合并初始余额和交易结果
    df_balance = pd.concat([initial_balance_df, df_result[['close_date', 'cumulative_pnl']]], ignore_index=True)
    df_balance = df_balance.sort_values('close_date').reset_index(drop=True)

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
    ax2.plot(df_balance['close_date'], df_balance['cumulative_pnl'], color=color, label='Balance')
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

def show_total_pnl(results, init_balance):
    """
    显示多 symbol 的总 PnL 曲线。
    
    参数：
    - results: 多 symbol 的交易结果字典，键为 symbol，值为交易结果列表。
    - init_balance: 初始资金。
    """

    # 创建一个空的 DataFrame，用于存储所有 symbol 的余额时间序列
    all_balances = pd.DataFrame()

    # 遍历每个 symbol 的交易结果
    for symbol, trades in results.items():
        df_trades = pd.DataFrame(trades)

        if df_trades.empty:
            print(f'No trading result for {symbol}')
            continue

        # 提取 'close_date' 和 'balance' 列，构建余额时间序列
        balance_series = df_trades[['close_date', 'balance']].copy()
        balance_series['close_date'] = pd.to_datetime(balance_series['close_date'])
        balance_series.set_index('close_date', inplace=True)

        # 添加初始余额点
        # 获取该 symbol 的最早交易日期
        earliest_date = balance_series.index.min()
        # 创建包含初始余额的 DataFrame
        initial_balance_df = pd.DataFrame({
            'balance': [init_balance]
        }, index=[earliest_date])

        # 将初始余额 DataFrame 与余额时间序列 DataFrame 合并
        balance_series = pd.concat([initial_balance_df, balance_series], axis=0)
        balance_series = balance_series.sort_index()
        # 去重（如果初始余额和第一个交易在同一天，会有重复的索引）
        balance_series = balance_series[~balance_series.index.duplicated(keep='first')]

        # 将该 symbol 的余额时间序列添加到 all_balances DataFrame 中
        balance_series = balance_series.rename(columns={'balance': symbol})
        all_balances = pd.concat([all_balances, balance_series], axis=1)

    if all_balances.empty:
        print('No trading data available.')
        return

    # 对齐所有 symbol 的日期索引
    all_balances = all_balances.sort_index()
    # 使用前向填充填充缺失值
    all_balances = all_balances.fillna(method='ffill')
    # 将初始缺失值填充为初始余额
    all_balances = all_balances.fillna(init_balance)

    # 获取所有的 symbol 列（排除可能存在的非 symbol 列）
    symbol_columns = [col for col in all_balances.columns if col != 'Total Balance']
    # 计算组合的总余额
    all_balances['Total Balance'] = all_balances[symbol_columns].sum(axis=1)

    # 绘制组合的总 PnL 曲线
    plt.figure(figsize=(15, 8))
    plt.plot(all_balances.index, all_balances['Total Balance'], label='Total Balance', color='black', linewidth=2)

    # 绘制每个 symbol 的余额曲线（可选）
    # for symbol in symbol_columns:
    #     plt.plot(all_balances.index, all_balances[symbol], label=f'{symbol} Balance', linestyle='--')

    plt.title('Total PnL Over Time')
    plt.xlabel('Date')
    plt.ylabel('Balance')
    plt.legend()
    plt.grid(True)
    plt.show()

def show_multi_symbol_pnl(results, init_balance):
    """
    显示多个 symbol 的 PnL 曲线
    """
    plt.figure(figsize=(15, 8))

    symbol_colors = {}  # 存储每个 symbol 的颜色

    # 获取所有交易的最早日期
    initial_dates = []
    for history in results.values():
        df = pd.DataFrame(history)
        if not df.empty:
            initial_dates.append(df['close_date'].min())
    if not initial_dates:
        print('No trading data available.')
        return
    initial_date = min(initial_dates)

    # 创建包含初始余额的 DataFrame
    initial_balance_df = pd.DataFrame({
        'close_date': [initial_date],
        'cumulative_pnl': [init_balance]
    })

    # 遍历每个 symbol 的回测结果
    for symbol, history in results.items():
        df = pd.DataFrame(history)

        if df.empty:
            print(f'No trading result for {symbol}')
            continue

        # 计算每个 symbol 的累计 PnL
        df['cumulative_pnl'] = df['pnl'].cumsum() + init_balance

        # 添加初始余额点
        df_symbol_balance = pd.concat([initial_balance_df, df[['close_date', 'cumulative_pnl']]], ignore_index=True)
        df_symbol_balance = df_symbol_balance.sort_values('close_date').reset_index(drop=True)

        # 为每个 symbol 分配颜色，并绘制 PnL 曲线
        color = plt.cm.tab10(len(symbol_colors) % 10)  # 从10种颜色中选择
        symbol_colors[symbol] = color
        plt.plot(df_symbol_balance['close_date'], df_symbol_balance['cumulative_pnl'],
                 label=f'{symbol} PnL', color=color)

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