import os
import time
import pandas as pd
from datetime import datetime, timedelta

from .utils.setup import init_ccxt_exchange
from .utils.folder import check_folder_exists, creat_folder, get_current_path

def get_klines(symbol=None, start=None, end=None, timeframe='1h', retry_count=3, pause=0.001, exchange_name='binanceusdm', proxy='http://127.0.0.1:7890/'):
    '''
      获取数据的对外接口, 在调用后, 先检查本地是否有相关的数据, 如果有数据, 则返回。如果没有相关数据, 调用fetch

      相关数据指的是同一交易对的同一时间周期, 且有部份时间重合的数据

      保存数据的目录是data-交易对-时间周期的三级结构
      目录命名: data > exchange_name-symbol > timeframe > 每天一个文件. 文件名为 YYYY-MM-DD-HH:MM - YYYY-MM-DD-HH:MM
      获取数据后自动保存, 加载

    Paramaters
    ------
      symbol: string
        交易对名称 e.g BTC/USDT, BTC_USDT
      start: string
        开始日期 format: YYYY-MM-DDTHH-MM-SSZ
      end: string
        结束日期 format: YYYY-MM-DDTHH-MM-SSZ
      timeframe: string
        K线时间周期: 1m, 5m, 15m, 1h, 4h 等等
      retry_count: int, 默认3
        遇到网络问题重复执行的次数
      pause: int 默认0.001
        重复请求中暂停的秒数, 防止请求过多导致限频
      exchange_name: string
        ccxt提的数据来源交易所关键字, 默认为币安期货
    '''

    exchange = init_ccxt_exchange(exchange_name, proxy)

    symbol_sp = symbol.split('/')
    current_path = get_current_path()
    data_path = f'{current_path}/data/{exchange_name}-{symbol_sp[0]}/{timeframe}'

    missing_periods = _check_local_data(data_path, start, end, timeframe)
    format_missing_periods = _format_missing_data(missing_periods)

    for period in format_missing_periods:
        start_time, end_time = period
        attempts = 0

        while attempts < retry_count:
            try:
                klines = _fetch_klines(symbol, start_time, end_time, timeframe, exchange)
                _save_data(data_path, klines)
                break
            except Exception as e:
                print(f'Error fetching data: {e}')
                attempts += 1
                time.sleep(pause)
    
    all_klines = _aggregate_data(data_path, start, end)
    
    # drop timestamp column
    all_klines = all_klines.drop(columns=['timestamp'])
    
    return all_klines

def aggregate_custom_timeframe(symbol, start, end, custom_timeframe, exchange_name='binanceusdm', proxy='http://127.0.0.1:7890/'):
    """
    聚合自定义时间周期的K线数据。
    
    参数:
    - symbol: 交易对名称，例如 'BTC/USDT'
    - start: 开始日期，格式 'YYYY-MM-DDTHH:MM:SSZ'
    - end: 结束日期，格式 'YYYY-MM-DDTHH:MM:SSZ'
    - custom_timeframe: 自定义的时间周期，例如 '2h', '3h'
    - exchange_name: 交易所名称，默认 'binanceusdm'
    - proxy: 代理服务器地址，例如 'http://127.0.0.1:7890/'
    """
    # 确定1分钟数据的存储路径
    timeframe = '1m'
    current_path = get_current_path()
    data_path = f'{current_path}/data/{exchange_name}-{symbol.replace("/", "_")}/{timeframe}'

    # 检查并拉取缺失的1分钟数据
    missing_periods = _check_local_data(data_path, start, end, timeframe)
    if missing_periods:
        format_missing_periods = _format_missing_data(missing_periods)
        exchange = init_ccxt_exchange(exchange_name, proxy)
        for period in format_missing_periods:
            start_time, end_time = period
            _fetch_klines(symbol, start_time, end_time, timeframe, exchange)

    # 聚合数据为自定义时间周期
    all_klines = _aggregate_data(data_path)
    aggregated_klines = all_klines.resample(custom_timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    return aggregated_klines

def _fetch_klines(symbol=None, start=None, end=None, timeframe='1h', exchange=None):
    '''
        获取单个头寸的K线
    Paramaters
    ------
      symbol: string
        交易对名称 e.g BTC/USDT, BTC_USDT
      start: string
        开始日期 format: YYYY-MM-DDTHH-MM-SSZ
      end: string
        结束日期 format: YYYY-MM-DDTHH-MM-SSZ
      timeframe: string
        K线时间周期: 1m, 5m, 15m, 1h, 4h 等等
      exchange: object
        ccxt提供的数据来源交易所, 默认为币安期货
    '''
    symbol = _check_symbol(symbol)
    start_date = pd.to_datetime(start, utc=True)
    end_date = pd.to_datetime(end, utc=True)

    start = exchange.parse8601(start)
    end = exchange.parse8601(end)

    klines = []
    while start < end:
        kline = exchange.fetch_ohlcv(symbol, timeframe, start)
        if len(kline) == 0:
            break
        
        klines += kline

        last_time = kline[-1][0]
        start = last_time + exchange.parse_timeframe(timeframe) * 1000

        if last_time >= end:
            break
    
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df.set_index('date', inplace=True, drop=True)

    df = df[(df.index >= start_date) & (df.index < end_date)]

    return df

def _check_symbol(symbol):
    if not symbol:
        raise Exception('No symbol', symbol)
    
    if '/' not in symbol and '_' not in symbol:
        print('Your symbol must like \'XXX_XXX\' or \'XXX/XXX\'')
        raise Exception('Wrong symbol', symbol)
    
    if '_' in symbol:
        return symbol.replace('_', '/')
    else:
        return symbol

def _save_data(path, df):
    """
    将文件保存在指定的目录中，目录命名: data > exchange_name-symbol > timeframe > 每天一个文件. 文件名为 YYYY/MM/DD/HH:MM - YYYY/MM/DD/HH:MM
    """
    if not check_folder_exists(path):
        creat_folder(path)
    
    for _, group in df.groupby(df.index.date):
        start_time = group.index.min()
        end_time = group.index.max()

        start_str = start_time.strftime('%Y-%m-%d-%H:%M')
        end_str = end_time.strftime('%Y-%m-%d-%H:%M')

        filename = f'{start_str} - {end_str}.csv'
        file_path = os.path.join(path, filename)

        group.to_csv(file_path)
        print(f'Data for {start_str} to {end_str} saved to {file_path}')

def _load_data(path):
    df = pd.read_csv(path, index_col='date', parse_dates=True)
    return df

def _aggregate_data(path, start, end):
    # 目前只支持整天的聚合，要在日内做数据切割还需要更新
    start = datetime.strptime(start, '%Y-%m-%dT%H:%M:%SZ')
    end = datetime.strptime(end, '%Y-%m-%dT%H:%M:%SZ')
    all_files = os.listdir(path)
    df_list = []

    all_files.sort()

    for file in all_files:
        file_start, file_end = _parse_time_range(file)
        if file_start >= start and file_end <= end:
            file_path = os.path.join(path, file)
            df = _load_data(file_path)
            df_list.append(df)

    all_df = pd.concat(df_list)
    all_df.sort_index(inplace=True)

    return all_df

def _check_local_data(path, start, end, timeframe):
    '''
    根据所需的参数, 检查本地是否有这些数据。如果没有, 则返回一个list, 指出缺失的部分
    '''
    missing_data = []
    
    if not check_folder_exists(path):
        creat_folder(path)

    start = datetime.strptime(start, '%Y-%m-%dT%H:%M:%SZ')
    end = datetime.strptime(end, '%Y-%m-%dT%H:%M:%SZ')
    timeframe_delta = _parse_timeframe(timeframe)
    
    # 调整结束日期为所需结束时间的前一天
    end_date_adjusted = end - timedelta(days=1)

    current_date = start
    while current_date <= end_date_adjusted:
        day_start = datetime(current_date.year, current_date.month, current_date.day)
        day_end = day_start + timedelta(days=1)
        covered = []

        # 检查这一天的所有文件
        for filename in os.listdir(path):
            file_start, file_end = _parse_time_range(filename)
            file_end_adj = file_end + timeframe_delta

            if day_start <= file_start < day_end or day_start < file_end_adj < day_end:
                covered.append((file_start, file_end_adj))

        # 检查缺失的时间段
        time_pointer = day_start
        while time_pointer < day_end:
            if not any(start <= time_pointer < end for start, end in covered):
                missing_start = time_pointer
                while time_pointer < day_end and not any(start <= time_pointer < end for start, end in covered):
                    time_pointer += timedelta(minutes=1)
                missing_end = time_pointer
                missing_data.append(f'{missing_start.strftime("%Y-%m-%d-%H:%M")} - {missing_end.strftime("%Y-%m-%d-%H:%M")}')
            else:
                time_pointer += timedelta(minutes=1)

        current_date += timedelta(days=1)
    
    return missing_data

def _parse_time_range(filename):
    '''
    从文件名解析该文件保存数据的时间范围
    '''
    filename = filename.rsplit('.', 1)[0]
    start, end = filename.split(' - ')
    start = datetime.strptime(start, '%Y-%m-%d-%H:%M')
    end = datetime.strptime(end, '%Y-%m-%d-%H:%M')

    return start, end

def _parse_timeframe(timeframe_str):
    """
    将时间周期字符串转换为timedelta对象。
    """
    if timeframe_str.endswith('m'):
        return timedelta(minutes=int(timeframe_str[:-1]))
    elif timeframe_str.endswith('h'):
        return timedelta(hours=int(timeframe_str[:-1]))
    elif timeframe_str.endswith('d'):
        return timedelta(days=int(timeframe_str[:-1]))
    else:
        raise ValueError(f"Unsupported timeframe: {timeframe_str}")
  
def _format_missing_data(missing_data):
    formatted_missing_data = []
    for period in missing_data:
        start_str, end_str = period.split(' - ')
        start_dt = datetime.strptime(start_str, '%Y-%m-%d-%H:%M')
        end_dt = datetime.strptime(end_str, '%Y-%m-%d-%H:%M')

        # 转换为所需的格式
        formatted_start = start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        formatted_end = end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        formatted_missing_data.append((formatted_start, formatted_end))

    return formatted_missing_data