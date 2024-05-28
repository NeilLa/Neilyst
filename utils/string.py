# 有关字符串处理的功能函数

def split_letters_numbers(s):
    """
    Split a string into two parts: the first part contains letters and
    the second part contains numbers.

    Args:
    s (str): The input string to split.

    Returns:
    tuple: A tuple containing two elements, the first is the letters part
           and the second is the numbers part of the input string.
    """
    # 找到第一个数字字符的索引
    for i, char in enumerate(s):
        if char.isdigit():
            # 返回分割后的两部分
            return s[:i], s[i:]
    # 如果没有数字，返回整个字符串和空字符串
    return s, ''
