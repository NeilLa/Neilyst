import re

def split_letters_numbers(s):
    """
    将指标名称和参数分开，支持多个参数。
    例如：
    - 'normalized_stddev14_14' => ('normalized_stddev', ['14', '14'])
    - 'normalized_stddev' => ('normalized_stddev', [])
    """
    # 使用正则表达式匹配指标名称和参数部分
    match = re.match(r'^([A-Za-z_]+)(?:_(\d+(?:_\d+)*))?$', s)
    if match:
        name = match.group(1)
        params_str = match.group(2)
        if params_str:
            params = params_str.split('_')
        else:
            params = []
        return name, params
    else:
        # 如果不匹配，返回原字符串作为名称，参数为空
        return s, []
