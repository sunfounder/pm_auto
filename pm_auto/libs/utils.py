import time
from typing import Optional

from importlib.resources import files as resource_files
from os import path
__package_name__ = __name__.split('.')[0]
ASSET_PATH = str(resource_files(__package_name__).joinpath('assets'))
ICON_PATH = path.join(ASSET_PATH, 'icons')
FONT_PATH  = path.join(ASSET_PATH, 'fonts')

def get_icon(name):
    return path.join(ICON_PATH, name)

def get_font(name):
    return path.join(FONT_PATH, name)

def map_value(x, from_min, from_max, to_min, to_max):
    return (x - from_min) * (to_max - to_min) / (from_max - from_min) + to_min

def log_error(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            if hasattr(self, 'log'):
                self.log.exception(str(e))
    return wrapper

def run_command(cmd):
    import subprocess
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode()
    status = p.poll()
    return status, result

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

def has_common_items(list1, list2):
    return bool(set(list1) & set(list2))

def constrain(value, min_value, max_value):
    return max(min(value, max_value), min_value)

class DebounceRunner():
    ''' Lazy reader. Read something in a given interval,
    even if you read it multiple times in a short time.
    For those who don't need to read it too frequently.
    '''
    def __init__(self, function, interval=10):
        ''' Initialize the lazy reader.

        Args:
            function (function): The function to read.
            interval (int): The interval to read.
        '''
        self.function = function
        self.interval = interval
        self.value = None
        self.last_read_time = 0

    def run(self):
        ''' Read the value.

        Returns:
            The value.
        '''
        if time.time() - self.last_read_time > self.interval:
            self.value = self.function()
            self.last_read_time = time.time()
        return self.value

    def __call__(self):
        return self.run()

RP1_GPIO_COMPATIBLE = 'raspberrypi,rp1-gpio'
GPIOZERO_PI5_CHIP = '/dev/gpiochip4'

def find_rp1_gpiochip() -> Optional[str]:
    ''' Return the /dev path of the Pi 5 header GPIO chip (RP1), or None.

    The kernel does not keep a stable number for this chip (gpiochip4,
    gpiochip0, gpiochip15...), so match it by its device tree compatible.
    '''
    from pathlib import Path
    for dev in sorted(Path('/sys/bus/gpio/devices').glob('gpiochip*')):
        compatible = dev / 'of_node' / 'compatible'
        if compatible.is_file() and \
                RP1_GPIO_COMPATIBLE in compatible.read_text().split('\0'):
            return f'/dev/{dev.name}'
    return None

def softlink_rp1_gpiochip_to_gpiochip4() -> None:
    ''' Point gpiochip4, which gpiozero opens on a Pi 5, at the RP1 chip. '''
    import os
    rp1_chip = find_rp1_gpiochip()
    if rp1_chip is None:
        return
    if os.path.realpath(GPIOZERO_PI5_CHIP) == os.path.realpath(rp1_chip):
        return
    if os.path.exists(GPIOZERO_PI5_CHIP) and not os.path.islink(GPIOZERO_PI5_CHIP):
        return
    try:
        if os.path.islink(GPIOZERO_PI5_CHIP):
            os.remove(GPIOZERO_PI5_CHIP)
        os.symlink(rp1_chip, GPIOZERO_PI5_CHIP)
    except OSError as e:
        raise Exception(f'Failed to softlink {rp1_chip} to {GPIOZERO_PI5_CHIP}: {e}') from e

# Former name, kept for external callers
softlink_gpiochip0_to_gpiochip4 = softlink_rp1_gpiochip_to_gpiochip4

def hex_to_rgb(hex):
    ''' str or hex, eg: 'ffffff', '#ffffff', '#FFFFFF' '''
    if not hex:
        raise Exception(f'Invalid hex color: "{hex}", must be str or hex, eg: "ffffff", "#ffffff", "#FFFFFF"')
    if isinstance(hex, str):
        hex = hex.strip().replace('#', '')
    r = int(hex[0:2], 16)
    g = int(hex[2:4], 16)
    b = int(hex[4:6], 16)
    return [r, g, b]
