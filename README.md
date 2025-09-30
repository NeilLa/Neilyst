# Neilyst重构开发文档

## 0. 背景
* 使用uv，ruff，pylance来做项目环境管理和代码审查
* 所有数据结构都定义原型
* 使用polars全面替代pandas
* 支持因子研究
* 对于时序cta策略，默认支持全市场回测，分symbol回测，并直接输出回测报告
* 对于统计套利等类似截面策略，也需要进行支持，并直接输入回测报告
* 支持交易参数寻优
* 大幅优化所有回测速度

## 1. 目录重构
neilyst/
├── pyproject.toml
├── README.md
├── .ruff.toml
├── .pre-commit-config.yaml
├── src/
│   └── neilyst/
│       ├── __init__.py
│       ├── core/                         # 引擎 & 共用协议层（稳定 API）
│       │   ├── engine.py                 # 回测主引擎（单/多symbol, 单/多策略）
│       │   ├── executor.py               # 执行器抽象：BacktestExecutor/LiveExecutor/SimLOB
│       │   ├── event.py                  # 事件：Bar, Trade, Order, Funding, Signal, Clock...
│       │   ├── models.py                 # Position/Order/Fill/Portfolio/Account/Leg/Condition
│       │   ├── config.py                 # pydantic 配置、全局常量
│       │   ├── pipeline.py               # 数据→指标→信号→执行 的流水线编排
│       │   ├── registry.py               # 注册表：指标/策略/因子/数据源/报告
│       │   └── utils.py                  # 公共小工具、时间/货币/滑点/费用等
│       ├── data/
│       │   ├── base.py                   # IDataSource/IBarStore 抽象
│       │   ├── ccxt_source.py            # 统一K线接口适配器（兼容现有 CCXT）
│       │   ├── binance_api.py            # 直连交易所 REST/WS 适配（替换/并存 CCXT）
│       │   ├── local_store.py            # Parquet/Feather 本地数据仓（读写分层）
│       │   ├── aggregator.py             # 自定义周期聚合（1m→5m/1h/自定义）
│       │   └── schemas.py                # TypedDict/pyarrow schema（时间、列名标准）
│       ├── indicators/
│       │   ├── base.py                   # IIndicator/批量计算协议 & 命名规范（sma_20 等）
│       │   ├── ta_wrappers.py            # pandas_ta 包装（统一命名、去重解决）
│       │   ├── lib/                      # 你的自建指标库（normalized_stddev_14_14 等）
│       │   │   └── __init__.py
│       │   └── registry.py               # 指标注册/解析（字符串→函数+参数）
│       ├── strategies/
│       │   ├── base.py                   # IStrategy：run() 返回向量化信号 [-1,1]
│       │   ├── examples/
│       │   │   └── double_ma.py          # 迁移你的 DoubleMa（同时演示信号向量）
│       │   └── policy/                   # 风控、仓位管理、止盈止损条件器（可组合）
│       ├── factors/
│       │   ├── base.py                   # IFactor & 因子元数据（频率、滞后、依赖列）
│       │   ├── library.py                # 常见横截面/时序因子
│       │   └── analyzer.py               # 因子评估：IC/IR、分层收益、打分卡
│       ├── portfolio/
│       │   ├── router.py                 # 多标的/多策略资金路由、权重、共线性分析
│       │   ├── risk.py                   # 账户/日风控、回撤/阈值、敞口合规
│       │   └── allocator.py              # Budget/目标杠杆/目标波动率分配
│       ├── report/
│       │   ├── evaluator.py              # 统一评估（APR/Sharpe/回撤/胜率/持仓时长…）
│       │   ├── html.py                   # HTML 报告（因子页、交易页、曲线页）
│       │   └── plots.py                  # 可视化：净值、分布、回撤、交易点、指标同步
│       ├── ml/
│       │   ├── online.py                 # 在线/滚动训练接口（策略可选择使用）
│       │   └── datasets.py               # 特征构建与窗口化、泄漏控制
│       └── cli/
│           └── neilyst_cli.py            # 命令行：取数/回测/评估/报告/网格搜索
├── tests/
│   ├── test_engine_single.py
│   ├── test_engine_multi.py
│   ├── test_indicators_registry.py
│   ├── test_strategy_contracts.py
│   └── test_report_evaluator.py
├── examples/
│   ├── 01_download_ccxt.py
│   ├── 02_build_indicators.py
│   ├── 03_backtest_double_ma.py
│   ├── 04_factor_ic_demo.py
│   └── 05_pair_trading_roll_train.py
└── scripts/
    ├── cache_data.sh
    └── make_report.sh
