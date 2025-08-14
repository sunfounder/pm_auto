from itertools import islice
import time

from pm_auto.libs.utils import get_icon, get_font
from pm_auto.libs.oled_page import OLEDPage

ethernet_icon = get_icon('icon_lan_20.png')
wifi_icon = get_icon('icon_wifi_20.png')
net_icon = get_icon('icon_network_20.png')
error_icon = get_icon('icon_error_20.png')

font = get_font('UbuntuSans-Regular.ttf')

class PageIPs(OLEDPage):
    def __init__(self):
        super().__init__()
        self.ip_index = 0
        self.ip_num = 0
        self.cycle_time_start = 0

    def main(self, oled, data, config):
        scroll_interval = config['scroll_interval']

        ips = data.get('ips', [])
        
        oled.clear()

        if len(ips) == 0:
            oled.draw_icon(error_icon, 53, 0, scale=1, invert=False, dither=False, threshold=50)
            oled.draw_text('DISCONNECTED', 14, 22, size=14, font_path=font)
        else:
            if self.ip_num != len(ips):
                self.ip_index = 0
                self.cycle_time_start = time.time()
                self.ip_num = len(ips)

            if time.time() - self.cycle_time_start >= scroll_interval:
                self.cycle_time_start = time.time()
                self.ip_index += 3
                if self.ip_index >= len(ips):
                    self.ip_index = 0

            _iter = islice(ips.items(), self.ip_index, self.ip_index + 3)

            for i in range(3):
                try:
                    interface, ip = next(_iter)
                    if interface.startswith('eth') or interface.startswith('en'):
                        oled.draw_icon(ethernet_icon, 0, i*22, scale=1, invert=False,  dither=False, threshold=80)
                        oled.draw_text(f'{ip}', 22, i * 22, size=14, font_path=font)
                    elif interface.startswith('wlan') or interface.startswith('wl'):
                        oled.draw_icon(wifi_icon, 0, i*22, scale=1, invert=False, dither=False, threshold=85)
                        oled.draw_text(f'{ip}', 22, i * 22, size=14, font_path=font)
                except StopIteration:
                    break

        oled.display()
