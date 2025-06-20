from itertools import islice
import time

from sf_rpi_status import get_disks_info
from .uilts import format_bytes

from pathlib import Path
grandparent_dir = Path(__file__).resolve().parent.parent
sdcard_icon = str(grandparent_dir) + '/icons/sdcard_icon_20.png'
nvme_icon = str(grandparent_dir) + '/icons/nvme_icon_20.png'
usb_stick_icon = str(grandparent_dir) + '/icons/usb_stick_icon_20.png'
error = str(grandparent_dir) + '/icons/error_icon_20.png'

disk_index = 0
disk_num = 0
cycle_time_start = 0

def oled_page_disk(oled, config):
    global disk_index, disk_num, cycle_time_start

    scroll_interval = config['scroll_interval']

    disks_info = get_disks_info()

    oled.clear()

    if len(disks_info) == 0:
        oled.draw_icon(error, 53, 0, scale=1, invert=False, dither=False, threshold=50)
        oled.draw_text('Disk Detection Error', 0, 22, size=14)
    else:
        if disk_num != len(disks_info):
            disk_index = 0
            cycle_time_start = time.time()
            disk_num = len(disks_info)

        if time.time() - cycle_time_start >= scroll_interval:
            cycle_time_start = time.time()
            disk_index += 3
            if disk_index >= len(disks_info):
                disk_index = 0

        _iter = islice(disks_info.items(), disk_index, disk_index + 3)

        for i in range(3):
            try:
                name, info = next(_iter)
                if 'mmcblk' in name:
                    oled.draw_icon(sdcard_icon, 0, i * 22, dither=False, threshold=130)
                elif 'nvme0' in name:
                    oled.draw_icon(nvme_icon, 0, i * 22+5, dither=False, threshold=130)
                    oled.draw_text(f'ssd 0', 1, i * 22, size=9)
                elif 'nvme1' in name:
                    oled.draw_icon(nvme_icon, 0, i * 22+5, dither=False, threshold=130)
                    oled.draw_text(f'ssd 1', 1, i * 22, size=9)
                elif 'sda' in name:
                    oled.draw_icon(usb_stick_icon, 0, i * 22, dither=False, threshold=100)

                _total, _uint = format_bytes(info.total)
                _used = format_bytes(info._used, _uint)
                oled.draw_text(f'{_used}/{_total} {_uint}', 32, i * 22, size=12)
                oled.draw_bar_graph_horizontal(info._percent, 26, i * 23 + 12, 100, 5)              
            except StopIteration:
                break

    oled.display()
    