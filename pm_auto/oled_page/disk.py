from sf_rpi_status import get_disks_info
from .oled_config import *
from .uilts import *

from pathlib import Path
grandparent_dir = Path(__file__).resolve().parent.parent
sdcard_icon = str(grandparent_dir) + '/icons/sdcard_icon_20.png'
nvme_icon = str(grandparent_dir) + '/icons/nvme_icon_20.png'
usb_stick_icon = str(grandparent_dir) + '/icons/usb_stick_icon_20.png'

def oled_page_disk(oled):
    disks_info = get_disks_info()

    oled.clear()

    i = 0
    for name, info in disks_info.items():
        # 是否包含
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
        i += 1

    oled.display()
    