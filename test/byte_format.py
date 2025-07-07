
def format_bytes_auto(size, auto_threshold=1024):
    # 定义字节单位
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    # 计算合适的单位
    unit = 0
    while size >= auto_threshold and unit < len(units)-1:
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

def format_bytes(size, to_unit=None, auto_threshold=1024):
    # 定义字节单位
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    # 如果目标单位有定义
    if to_unit and to_unit in units:
        return format_bytes_fix(size, to_unit)
    # 如果目标单位未定义
    else:
        return format_bytes_auto(size, auto_threshold=auto_threshold)

def big_number(number):
    # 给大数字，每3位数增加逗号分隔
    number_str = "{:,}".format(number)
    return number_str

def main():
    import math
    # test_list = [1, 100, 500, 1000, 5000, 1000000, 5000000, 1000000000, 5000000000, 1000000000000, 500000000000000, 100000000000000000, 500000000000000000]
    test_list = [math.pow(10, i) for i in range(1, 21)]
    for i in test_list:
        formated, unit = format_bytes(i, auto_threshold=100)

        print(f"{big_number(i)} -> {formated} {unit}")

if __name__ == "__main__":
    main()
