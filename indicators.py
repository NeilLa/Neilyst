import pandas_ta as ta
import pandas as pd
import os
import inspect
import sys
from .utils.string import split_letters_numbers

# 将自建指标库添加到Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
indicators_lib_path = os.path.join(current_dir, 'indicators_lib')
sys.path.append(indicators_lib_path)

def get_indicators(data, *args):
    """
    对外的计算指标的接口，支持单个或多个 symbol。
    """
    if isinstance(data, dict):
        # 多 symbol 情况
        all_indicators = {}
        for symbol, df in data.items():
            indicators_df = _calculate_indicators_for_single_symbol(df, *args)
            all_indicators[symbol] = indicators_df

        return all_indicators
    else:
        # 单 symbol 情况
        return _calculate_indicators_for_single_symbol(data, *args)

def _calculate_indicators_for_single_symbol(data, *args):
    """
    计算单个 symbol 的指标。
    """
    indicators = args
    indicators_df = pd.DataFrame()
    indicators_df['close'] = data['close']

    for indicator in indicators:
        name, length = split_letters_numbers(indicator)
        length = int(length) if length else None
        col_name = f'{name}{length}' if length else f'{name}'

        if hasattr(ta, name):
            func = getattr(ta, name)
        else:
            # 再pandas_ta中找不到指标 则尝试在自建指标库中搜索
            try:
                custom_indicator_module = __import__(name)
                func = getattr(custom_indicator_module, name)
            except ImportError:
                print(f'Indicator {name} not found in pandas_ta or indicators_lib.')
                continue
            except AttributeError:
                print(f'Function {name} not found in module {name}.')
                continue
        try:
            # 获取函数签名
            sig = inspect.signature(func)
            required_params = sig.parameters

            # 构建传入的参数，根据函数所需的参数动态传递
            kwargs = {}
            if 'length' in required_params and length is not None:
                kwargs['length'] = length

            # 根据函数签名传递数据列 (open, high, low, close, volume)
            if 'open' in required_params:
                kwargs['open'] = data['open']
            if 'high' in required_params:
                kwargs['high'] = data['high']
            if 'low' in required_params:
                kwargs['low'] = data['low']
            if 'close' in required_params:
                kwargs['close'] = data['close']
            if 'volume' in required_params and 'volume' in data.columns:
                kwargs['volume'] = data['volume']

            # 调用指标函数
            result = func(**kwargs)
            if result is None:
                print(f'Indicator {name} returned None.')
                continue

            # 处理返回多个列的情况
            if isinstance(result, pd.DataFrame):
                for col in result.columns:
                    indicators_df[f'{col_name}_{col}'] = result[col]
            else:
                indicators_df[col_name] = result

            # 填充空值
            indicators_df = indicators_df.fillna(method='bfill')
        except Exception as e:
            print(f'Error calculating indicator {name}: {e}')

    return indicators_df

    