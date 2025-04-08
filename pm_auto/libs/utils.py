
def map_value(x, from_min, from_max, to_min, to_max):
    return (x - from_min) * (to_max - to_min) / (from_max - from_min) + to_min

def log_error(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self.log.exception(str(e))
    return wrapper

def run_command(cmd):
    import subprocess
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode()
    status = p.poll()
    return status, result

def format_bytes_auto(size):
    # 定义字节单位
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    # 计算合适的单位
    unit = 0
    while size >= 1024 and unit < len(units)-1:
        size /= 1024
        unit += 1
    # 格式化为带有一位小数的字符串
    size = f"{size:.1f}"
    unit = units[unit]
    return size, unit

def format_bytes_fix(size, to_unit=None):
    # 定义字节单位
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    # 计算目标单位的索引
    to_index = units.index(to_unit)
    for _ in range(to_index):
        size /= 1024

    # 格式化为带有一位小数的字符串
    size = f"{size:.1f}"
    return size

def format_bytes(size, to_unit=None):
    # 定义字节单位
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    # 如果目标单位有定义
    if to_unit and to_unit in units:
        return format_bytes_fix(size, to_unit)
    # 如果目标单位未定义
    else:
        return format_bytes_auto(size)

def has_common_items(list1, list2):
    return bool(set(list1) & set(list2))
