# Neilyst

## 简介

这是一个用于量化交易策略回测的框架，支持多币种和单币种的历史数据回测。框架提供了多种技术指标的计算、历史数据获取、回测执行、策略评估以及可视化功能。用户可以根据自己的需求轻松扩展策略，并通过已有的工具分析回测结果。

## 目录结构

```
.
├── __init__.py
├── analyze.py               # 策略实盘交易历史的分析工具
├── backtest.py              # 回测引擎的实现，包括多symbol支持
├── data.py                  # 历史K线数据获取模块
├── indicators.py            # 技术指标计算模块，支持单币种和多币种
├── indicators_lib/          # 自定义指标库
│   ├── __init__.py
├── models.py                # 核心模型，包括仓位、信号和策略的定义
├── utils/                   # 工具库，包括数据处理和文件管理等
│   ├── folder.py
│   ├── magic.py
│   ├── pandas_ta.py
│   ├── setup.py
│   └── string.py
└── visualize.py             # 回测结果和技术指标的可视化工具
```

## 安装与依赖

### 依赖库

1. `ccxt` - 用于从交易所获取历史K线数据
2. `pandas` - 数据处理
3. `pandas_ta` - 技术指标计算库
4. `matplotlib` - 数据可视化
5. `numpy` - 数值计算
6. `tqdm` - 进度条显示

使用以下命令安装依赖：

```bash
pip install ccxt pandas pandas_ta matplotlib numpy tqdm
```

## 使用方法

### 1. 获取历史数据

使用 `data.py` 中的 `get_klines()` 函数从交易所获取K线数据。此函数支持单币种和多币种，数据获取后将自动保存至本地文件系统。

示例：

```python
from data import get_klines

symbol = 'BTC/USDT'
start_time = '2023-01-01T00:00:00Z'
end_time = '2023-12-31T23:59:59Z'

# 获取1小时K线数据
data = get_klines(symbol, start_time, end_time, timeframe='1h')
```

### 2. 计算技术指标

在 `indicators.py` 中，`get_indicators()` 函数用于计算技术指标。框架支持对单币种和多币种计算技术指标，您可以直接传入数据并指定所需的指标。

示例：

```python
from indicators import get_indicators

# 计算BTC的简单移动平均线和相对强弱指数
indicators = get_indicators(data, 'sma20', 'rsi14')
```

### 3. 编写策略

策略的定义在 `models.py` 中。每个策略应继承 `Strategy` 类，并实现 `run()` 方法。该方法将接收当前数据行、当前仓位、当前余额等参数，并返回交易信号。

示例：

```python
from models import Strategy, Signal

class MyStrategy(Strategy):
    def run(self, date, price_row, current_pos, current_balance):
        # 实现你的交易策略逻辑
        if price_row['sma20'] > price_row['sma50']:
            return Signal('long', price_row['close'], current_balance / price_row['close'])
        elif price_row['sma20'] < price_row['sma50']:
            return Signal('short', price_row['close'], current_balance / price_row['close'])
        return None
```

### 4. 运行回测

使用 `backtest.py` 中的 `backtest()` 函数运行回测。框架支持单币种和多币种的回测。

```python
from backtest import backtest
from models import MyStrategy

# 初始化策略
strategy = MyStrategy(total_balance=1000, trading_fee_ratio=0.001, slippage_ratio=0.001)

# 运行回测
result = backtest(symbol='BTC/USDT', start='2023-01-01', end='2023-12-31', strategy=strategy)
```

### 5. 分析回测结果

使用 `analyze.py` 中的分析函数计算回测结果的各项指标，如盈亏比、胜率等。

```python
from analyze import calculate_win_rate

# 计算胜率
win_rate = calculate_win_rate(result)
print(f'胜率: {win_rate * 100:.2f}%')
```

### 6. 可视化回测结果

使用 `visualize.py` 中的可视化工具绘制回测结果和技术指标。

```python
from visualize import show_pnl

# 显示回测期间的盈亏曲线
show_pnl(data, result, init_balance=1000)
```

## 模块说明

### `analyze.py`

用于分析策略的实盘交易历史，提供计算盈亏比、胜率等接口。主要功能包括：

- `calculate_profit_loss_ratio()`：计算盈亏比
- `calculate_win_rate()`：计算胜率
- `load_history()`：加载历史交易数据

### `backtest.py`

回测引擎的核心，实现了策略的执行和回测逻辑。支持单币种和多币种回测，主要功能包括：

- `backtest()`：回测主入口，支持单个或多个交易对。
- `_single_symbol_engine()`：单个交易对的回测逻辑。
- `_multi_symbol_engine()`：多个交易对的回测逻辑。

### `data.py`

负责从交易所获取历史K线数据并存储到本地。主要功能包括：

- `get_klines()`：从交易所拉取K线数据。
- `aggregate_custom_timeframe()`：聚合数据为自定义时间周期。
- `_fetch_klines()`：获取单个交易对的K线数据。

### `indicators.py`

封装了技术指标的计算逻辑，支持单币种和多币种的技术指标计算。主要功能包括：

- `get_indicators()`：对外的技术指标计算接口。
- `_calculate_indicators_for_single_symbol()`：计算单个交易对的指标。

### `models.py`

定义了回测中的常用模型，包括仓位、信号和策略等核心类。主要功能包括：

- `Strategy`：抽象策略类，用户需继承此类并实现 `run()` 方法。
- `Signal`：定义交易信号。
- `Position`：用于记录仓位信息和盈亏计算。

### `visualize.py`

用于回测结果和技术指标的可视化，主要功能包括：

- `show_pnl()`：显示单币种的盈亏曲线。
- `show_multi_symbol_pnl()`：显示多个交易对的盈亏曲线。

### `utils/`

提供一些通用的辅助函数，如数据处理、文件操作等。主要功能包括：

- `folder.py`：文件管理工具。
- `magic.py`：包含一些常量和配置。
- `pandas_ta.py`：技术指标辅助工具。
- `setup.py`：框架的设置管理。

## 贡献

如果您有新的想法或改进建议，欢迎贡献代码。您可以通过提交 `pull request` 的方式参与项目改进。

## 许可证

本项目基于 MIT 许可证开源。

---

这是一个完整的 `README` 文件草稿，您可以根据实际需求进一步修改和完善。如果有需要调整的地方，随时告诉我。