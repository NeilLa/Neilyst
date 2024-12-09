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
# 2024.10.30: 现在指标和参数需要使用下划线进行分割, 并支持多个参数
indicators = get_indicators(data, 'sma_20', 'rsi_14')
```

### 3. 编写策略

策略的定义在 `models.py` 中。每个策略应继承 `Strategy` 类，并实现 `run()` 方法。该方法将接收当前数据行、当前仓位、当前余额等参数，并返回交易信号。

示例：

```python
from models import Strategy, Signal

# 策略class，一定要继承Neilyst.Strategy
class DoubleMa(Neilyst.Strategy):
    def __init__(self, total_balance, trading_fee_ratio, slippage_ratio, data=None, indicators=None):
        super().__init__(total_balance, trading_fee_ratio, slippage_ratio, data, indicators)
        self.total_balance = total_balance
        self.data = data
        self.indicators = indicators
    
    def run(self, date, price_row, current_pos, current_balance, symbol):
        recent_data = self.get_recent_data(date, 10, self.data, self.indicators, symbol)  # 获取最近10条k线数据和指标数据
        signal = None

        if len(recent_data) >= 3:
            # 获取最近的指标值
            # 为了能跟实盘对应上，这里最新的一条k线默认是取-2
            current_ma20 = recent_data.iloc[-2]['sma20']
            current_ma60 = recent_data.iloc[-2]['sma60']

            # 因此，前一条均线就是取的-3
            prev_ma20 = recent_data.iloc[-3]['sma20']
            prev_ma60 = recent_data.iloc[-3]['sma60']
            
            if current_pos.amount > 0:
                # 此时有仓位，考虑平仓过程
                # current_pos是一个class，具体的结构在model里面可以看到
                # current_pos.dir是当前有的仓位的方向
                # current_pos.amount这个属性表示的是当前仓位的数量
                if current_pos.dir == 'long':
                    if current_ma20 < current_ma60:
                        signal = Neilyst.Signal('close', price_row['close'], current_pos.amount)
                elif current_pos.dir == 'short':
                    if current_ma20 > current_ma60:
                        signal = Neilyst.Signal('close', price_row['close'], current_pos.amount)
                # 这里的signal是返回的下单信号，三个参数分别是下单方向，下单价格，下单量
                # 本框架会一直调用1min数据用来模拟ticker数据，price_row['close']指的就是当前分钟的收盘价
                # 这样滑点会比直接使用data里面的close小一些，更加贴近实盘
            else:
                # 没有仓位，考虑开仓信号
                # 这里的total_balance是策略运行时输入的初始余额
                # 如果每次都用它来计算pos值就相当于每单都以固定的数额下单
                # 如果想测试滚仓效果可以使用current_balance这个变量
                # 这个变量表示当前所剩全部余额
                pos = abs(self.total_balance / price_row['close'])
                if current_ma20 > current_ma60 and prev_ma20 < prev_ma60:
                        signal = Neilyst.Signal('long', price_row['close'], pos)
                if current_ma20 < current_ma60 and prev_ma20 > prev_ma60:
                        signal = Neilyst.Signal('short', price_row['close'], pos)
        
        # 最终返回一个signla
        # 没有信号就返回None
        return signal
    
    def pos_management(self, current_balance):
        # 这里是仓位管理函数
        # 可以按需求计算仓位
        pass
```

### 4. 运行回测

使用 `backtest.py` 中的 `backtest()` 函数运行回测。框架支持单币种和多币种的回测。

```python
from backtest import backtest
from models import MyStrategy

# 初始化策略
init_balance = 200
strategy = DoubleMa(init_balance, 0.005, 0.01, data, indicators)

# 运行回测
result = Neilyst.backtest(symbol, start_time, end_time, strategy)

# 计算结果
evaluation = Neilyst.evaluate_strategy(result, init_balance)
```

### 5. 可视化回测结果

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

## 下一个版本更新需求
1. 对于数据获取部分，可以引入直接使用币安API来拉数据，这样能够支持更多的数据种类。而且目前回测似乎不需要多个市场的数据。
   1. 对于引入api，不同交易所的api接口应该统一，即对于同一个功能的接口应该有统一的命名，返回统一的格式。
2. 对于指标计算部分，目前指标计算出来的指标名，还有重复的问题。
3. 对于回测部分，首先目前回测速度太慢。需要加快回测速度，针对单symbol回测似乎只能用向量化来加快速度（Cython?），多symbol应该使用多进程来优化速度。其次有关pnl，balance的计算应该统一时间，方便可视化的。另外，对于回测返回的信号，应该是一个向量，这个向量的结构应该与实盘相同，而且买卖信号应该是一个-1~1之间的值，并不是buy和sell。同时对于回测策略的参数属于应该标准化，每次输入什么参数，不应该在策略里面改，而是在策略外面进行修改。这样做的目的是我们在调试策略时，应该自动化的保存策略的测试结果和对应参数。这样能够更方便的进行策略比对和参数调优。
4. 针对中性策略、指增策略和统计套利等需要开多个仓位以及需要大量symbol的策略来说，回测系统应该能够同时管理多个仓位。而且迭代多个symbol的数据。所以也许需要仓位id来进行仓位识别。并且下单时可以添加止盈止损条件？
5. 针对因子分析，框架应该支持一份完整的因子分析流程。并且自动生成报告（html?）并且自动累计因子库。
6. 针对回测结果，应该有调试模式（同时输出开平仓时的指标值）？以及目前的模式。
7. 实现一个期权组合收益模拟器？
8. 有关多策略系统，需要高速生成多策略信号矩阵（向量计算），输出策略共线性，以及加权等等。
9.  考虑要支持机器学习算法（在策略运行时，一边学习一边回测） 

### Pair Trading
1. 首先为了避免使用未来数据，引擎应该支持滚动训练，具体的滚动训练的方法（使用的指标，例如corr，或者协整性等等）应该由策略决定，引擎只负责训练并返回结果。
2. 为了换symbol，引擎的输入应该是universe data
3. 协整期间买卖的指数，例如价格偏离等等，也应该由策略指定
4. 可以先规定好策略格式，然后倒推看看引擎应该怎么样实现

### 回测框架接口格式
UniverseSymbolPool->ChooseSymbolsLogicEngin->List(Dict(symbol1: value), Dict(symbol2: value))->TradeLogic->SignalTuple
   
## 贡献

如果您有新的想法或改进建议，欢迎贡献代码。您可以通过提交 `pull request` 的方式参与项目改进。

## 更新日志
2024.10.16  
fix bug: 现在get_recent_data里面不会有重复的close列了

2024.10.18  
update: 现在策略评估新增了交易次数和日均交易次数两个新指标，同时支持多币种  
fix: 修复了设置不同的proxy后，backtest拉取1min数据错误的问题，现在backtest函数也支持输入新的proxy变量了  

2024.10.30  
update: 现在支持使用自建的指标库了，自建指标库为indicators_lib，当get_indicators无法从pandas_ta获取相应指标时，会从indicators_lib中再搜索一次  
update: 更新了归一化ATR指标，首先计算了价格序列的标准差，再计算相同长度窗口的ATR，获取市场的平均波动性，然后再使用标准差/ATR，就得到了归一化的标准差。可以用来衡量归一化的波动性。并且，由于该指标需要两个参数，现在get_indicators支持多个参数的输入了。并且输入格式也进行了相应的改变。  
e.g:
``` Python
indicators = Neilyst.get_indicators(data, 'ohlc_ema_8', 'ohlc_ema_30', 'normalized_stddev_14_14')
```

2024.11.07  
update: 现在Pnl可视化会从初始资金开始画图而不是第一次交易之后的余额。

2024.11.08  
fix: 修复了一个计算年化收益率的bug，现在年化收益率的结果应当是正确的了。  
add: 新增了show_total_pnl方法，现在可以显示多symbol的总净值曲线了。  
add: 新增了show_return_distribution方法，现在可以显示收益率的分布直方图了。  
update: 现在单symbol回测结果评估新增了如下指标：平均持仓时长（按小时计），最大持仓时间，单次最大盈利（盈利数额，发生时间），单次最大亏损（亏损数额，发生时间）。
