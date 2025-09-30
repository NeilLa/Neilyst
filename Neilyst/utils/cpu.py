import psutil
import multiprocessing

def get_available_cpu_count(cpu_usage_limit=80):
    # 计算在当前使用场景下 CPU还有多少算力剩余
    # 输入的参数为设置的允许CPU算力的最大百分比
    total_cpus = multiprocessing.cpu_count()
    current_cpu_usage = psutil.cpu_percent(interval=1)

    available_cpu_percentage = max(0, cpu_usage_limit - current_cpu_usage)

    available_cpus = int((available_cpu_percentage / 100) * total_cpus)

    return max(1, available_cpus)