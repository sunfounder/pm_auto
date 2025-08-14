from itertools import islice
import time

from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_icon, format_bytes, get_font

sdcard_icon = get_icon('icon_sd_card_20.png')
nvme_icon = get_icon('icon_hard_drive_20.png')
usb_stick_icon = get_icon('icon_usb_disk_20.png')
hard_disk_icon = get_icon('icon_hard_drive_20.png')
raid_icon = get_icon('icon_raid_20.png')
error_icon = get_icon('icon_error_20.png')

font = get_font('UbuntuSans-Regular.ttf')

class PageDisks(OLEDPage):
    def __init__(self):
        super().__init__()
        self.disk_index = 0
        self.disk_num = 0
        self.cycle_time_start = 0

    def main(self, oled, data, config):
        scroll_interval = config['scroll_interval']

        disks_info = data.get('disks', [])

        oled.clear()

        if len(disks_info) == 0:
            oled.draw_icon(error_icon, 53, 0, scale=1, invert=False, dither=False, threshold=50)
            oled.draw_text('Disk Detection Error', 0, 22, size=14, font_path=font)
        else:
            if self.disk_num != len(disks_info):
                self.disk_index = 0
                self.cycle_time_start = time.time()
                self.disk_num = len(disks_info)

            if time.time() - self.cycle_time_start >= scroll_interval:
                self.cycle_time_start = time.time()
                self.disk_index += 3
                if self.disk_index >= len(disks_info):
                    self.disk_index = 0

            _iter = islice(disks_info.items(), self.disk_index, self.disk_index + 3)

            for i in range(3):
                try:
                    name, info = next(_iter)
                    if info.type == 'sd':
                        oled.draw_icon(sdcard_icon, 0, i * 22, dither=False, threshold=130)
                    elif info.type == 'nvme':
                        oled.draw_icon(nvme_icon, 0, i * 22+5, dither=False, threshold=130)
                    elif info.type == 'usb':
                        oled.draw_icon(usb_stick_icon, 0, i * 22, dither=False, threshold=100)
                    elif info.type == 'hd':
                        oled.draw_icon(hard_disk_icon, 0, i * 22, dither=False, threshold=100)
                    elif info.type == 'raid':
                        oled.draw_icon(raid_icon, 0, i * 22, dither=False, threshold=100)

                    _total, _uint = format_bytes(info.total)
                    _used = format_bytes(info._used, _uint)
                    oled.draw_text(f'{_used}/{_total} {_uint}', 32, i * 22, size=12, font_path=font)
                    oled.draw_bar_graph_horizontal(info._percent, 26, i * 23 + 12, 100, 5)              
                except StopIteration:
                    break

        oled.display()
        