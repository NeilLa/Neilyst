import os
import time
import pandas as pd
from datetime import datetime, timedelta

from .utils.setup import init_ccxt_exchange
from .utils.folder import check_folder_exists, creat_folder, get_current_path

def get_klines(symbol=None, start=None, end=None, timeframe='1h', auth=True, retry_count=3, pause=0.001, exchange_name='binanceusdm', proxy='http://127.0.0.1:7890/', data_path=None):
    """
    获取单个或多个 symbol 的 K 线数据。
    
    参数:
    - symbol: string 或 list, 交易对名称或交易对名称列表 e.g 'BTC/USDT' 或 ['BTC/USDT', 'ETH/USDT']
    - start: string, 开始日期 format: YYYY-MM-DDTHH-MM-SSZ
    - end: string, 结束日期 format: YYYY-MM-DDTHH-MM-SSZ
    - timeframe: string, K线时间周期: 1m, 5m, 15m, 1h, 4h 等等
    - auth: bool, 是否验证数据的完整性, 默认为 True
    - retry_count: int, 遇到网络问题重复执行的次数, 默认 3
    - pause: int, 重复请求中暂停的秒数, 默认 0.001
    - exchange_name: string, ccxt提的数据来源交易所关键字, 默认为币安期货
    - proxy: string, 代理服务器地址, 默认为 'http://127.0.0.1:7890/'
    """
    if isinstance(symbol, str):
        # 处理单个 symbol 的情况
        return _get_single_symbol_klines(symbol, start, end, timeframe, auth, retry_count, pause, exchange_name, proxy, data_path)
    elif isinstance(symbol, list):
        # 处理多个 symbol 的情况
        all_data = {}
        for sym in symbol:
            data = _get_single_symbol_klines(sym, start, end, timeframe, auth, retry_count, pause, exchange_name, proxy, data_path)
            all_data[sym] = data

        return all_data
    else:
        raise ValueError("symbol 参数必须是字符串或列表")

def aggregate_custom_timeframe(symbol, start, end, custom_timeframe, exchange_name='binanceusdm', proxy='http://127.0.0.1:7890/', auth=True, data_path=None):
    """
    聚合自定义时间周期的K线数据。
    """
    # 确定1分钟数据的存储路径
    timeframe = '1m'
    symbol_sp = symbol.split('/')
    if data_path is None:
        # 使用默认路径
        current_path = get_current_path()
        data_path_1m = f'{current_path}/data/{exchange_name}-{symbol_sp[0]}/{timeframe}'
    else:
        # 使用传入的 data_path，并添加子目录
        data_path_1m = os.path.join(data_path, f'{exchange_name}-{symbol_sp[0]}', timeframe)

    # 检查并拉取缺失的1分钟数据
    if auth:
        missing_periods = _check_local_data(data_path_1m, start, end, timeframe)
        if missing_periods:
            format_missing_periods = _format_missing_data(missing_periods)
            exchange = init_ccxt_exchange(exchange_name, proxy)
            for period in format_missing_periods:
                start_time, end_time = period
                klines_1m = _fetch_klines(symbol, start_time, end_time, timeframe, exchange)
                _save_data(data_path_1m, klines_1m)
    # 聚合数据为自定义时间周期
    all_klines = _aggregate_data(data_path_1m, start, end)
    custom_minutes = _convert_to_minutes(custom_timeframe)
    aggregated_klines = _custom_resampler(all_klines, custom_minutes)

    # 将原始index设置为对应的时间点
    aggregated_klines.index = all_klines.index[::custom_minutes][:len(aggregated_klines)]

    # 保存聚合后的数据
    if data_path is None:
        custom_data_path = f'{current_path}/data/{exchange_name}-{symbol_sp[0]}/{custom_timeframe}'
    else:
        custom_data_path = os.path.join(data_path, f'{exchange_name}-{symbol_sp[0]}', custom_timeframe)

    _save_data(custom_data_path, aggregated_klines)

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

def _get_single_symbol_klines(symbol=None, start=None, end=None, timeframe='1h', auth=True, retry_count=3, pause=0.001, exchange_name='binanceusdm', proxy='http://127.0.0.1:7890/', data_path=None):
    """
    获取单个 symbol 的 K 线数据。
    """
    exchange = init_ccxt_exchange(exchange_name, proxy)
    symbol_sp = symbol.split('/')

    if data_path is None:
        # 使用默认路径
        current_path = get_current_path()
        data_path = f'{current_path}/data/{exchange_name}-{symbol_sp[0]}/{timeframe}'
    else:
        # 使用传入的 data_path，并添加子目录
        data_path = os.path.join(data_path, f'{exchange_name}-{symbol_sp[0]}', timeframe)

    if auth:
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
                    print(f'Error fetching data for {symbol}: {e}')
                    attempts += 1
                    time.sleep(pause)

    all_klines = _aggregate_data(data_path, start, end)

    # drop timestamp column
    if 'timestamp' in all_klines.columns:
        all_klines = all_klines.drop(columns=['timestamp'])

    return all_klines

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

def _convert_to_minutes(timeframe_str):
    """
    将自定义时间周期转换为分钟单位。
    支持的时间单位: 分钟m、小时h、天d、周w、月m
    """
    unit = timeframe_str[-1]
    amount = float(timeframe_str[:-1])

    if unit == 'm':  # 分钟
        return int(amount)
    elif unit == 'h':  # 小时
        return int(amount * 60)
    elif unit == 'd':  # 天
        return int(amount * 1440)  # 1天 = 1440分钟
    elif unit == 'w':  # 周
        return int(amount * 10080)  # 1周 = 10080分钟
    elif unit == 'M':  # 月（按30天计算）
        return int(amount * 43200)  # 1月 = 43200分钟（30天）
    else:
        raise ValueError(f"Unsupported timeframe: {timeframe_str}")
    
def _custom_resampler(data, custom_minutes):
    # 自定义时间窗口数据聚合器
    resampled = []
    for i in range(0, len(data), custom_minutes):
        chunk = data.iloc[i:i + custom_minutes]
        resampled.append({
            'open': chunk['open'].iloc[0],
            'high': chunk['high'].max(),
            'low': chunk['low'].min(),
            'close': chunk['close'].iloc[-1],
            'volume': chunk['volume'].sum()
        })
    return pd.DataFrame(resampled)