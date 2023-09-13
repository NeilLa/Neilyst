# Neilyst
基于Python和ccxt的全市场量化回测框架

## 1. 简介
这将是我本人的量化回测框架，主要功能将包括数据获取，数据落盘，数据清洗，时间序列聚合，指标计算，数据可视化，策略评估等。至于策略的运行引擎部分，实现有些过于复杂，暂时可以手动，以后如果有机会再慢慢实现。

## 2. 文件层级

Neilyst/
|-- neilyst/
|   |-- __init__.py
|
|   |-- DataManager/
|   |   |-- __init__.py
|   |   |-- fetcher.py     # 数据获取功能
|   |   |-- cleaner.py     # 数据清洗功能
|   |   |-- aggregator.py  # 时间序列聚合功能
|
|   |-- Analytics/
|   |   |-- __init__.py
|   |   |-- indicators.py  # 指标计算功能
|   |   |-- visualizer.py  # 数据可视化功能
|
|   |-- Strategy/
|   |   |-- __init__.py
|   |   |-- evaluator.py   # 策略评估功能
|   |   |-- example_strategy.py  # 示例策略
|
|-- tests/                 # 单元测试和其他测试
|   |-- data_manager/
|   |-- analytics/
|   |-- strategy/
|
|-- config/
|   |-- settings.py        # 配置文件，例如API密钥，数据库配置等
|
|-- setup.py               # Python包的安装和配置脚本
|-- README.md
