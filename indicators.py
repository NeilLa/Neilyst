import pandas_ta as ta
import pandas as pd
from .utils.string import split_letters_numbers

def get_indicators(data, *args):
    """
    对外的计算指标的接口
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
            try:
                if name in ['supertrend']:  # 需要传递ohlc数据的指标
                    if length is not None:
                        result = func(data['high'], data['low'], data['close'], length=length)
                    else:
                        result = func(data['high'], data['low'], data['close'])
                else:  # 只需要收盘价数据的指标
                    if length is not None:
                        result = func(data['close'], length=length)
                    else:
                        result = func(data['close'])

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
        else:
            print(f'Indicator {name} not found in pandas_ta.')

    return indicators_df

