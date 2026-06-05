from itertools import islice
import time

from pm_auto.libs.utils import get_icon, get_font
from pm_auto.libs.oled_page import OLEDPage

font = get_font('UbuntuSans-Regular.ttf')

ethernet_icon = get_icon('icon_lan_20.png')
wifi_icon = get_icon('icon_wifi_20.png')
net_icon = get_icon('icon_network_20.png')
cpu_icon = get_icon('icon_cpu_24.png')
temp_icon = get_icon('icon_temperature_24.png')
ram_icon = get_icon('icon_ram_24.png')
error_icon = get_icon('icon_error_20.png')

class PageMix(OLEDPage):
    needs_ip = True

    def __init__(self):
        super().__init__()
        self.ip_index = 0
        self.ip_num = 0
        self.cycle_time_start = 0

    def main(self, oled, data, config):
        scroll_interval = config['scroll_interval']
        temperature_unit = config['temperature_unit']

        ips = data.get('ips', [])

        cpu_temp_c = data.get("cpu_temperature", 0)
        cpu_temp_f = cpu_temp_c * 9 / 5 + 32
        cpu_usage = data.get("cpu_percent", 0)
        if cpu_usage >= 100:
            cpu_usage = 100

        temp = cpu_temp_c if temperature_unit == 'C' else cpu_temp_f
        temp = round(temp, 1)

        memory_percent = data.get("memory_percent", 0)
        if memory_percent >= 100:
            memory_percent = 100

        oled.clear()

        # ips
        if len(ips) == 0:
            oled.draw_icon(error_icon, 0, 0, scale=1, invert=False, dither=False, threshold=50)
            oled.draw_text('DISCONNECTED', 22, 0, size=14, font_path=font)
        else:
            if self.ip_num != len(ips):
                self.ip_index = 0
                self.cycle_time_start = time.time()
                self.ip_num = len(ips)

            if time.time() - self.cycle_time_start >= scroll_interval:
                self.cycle_time_start = time.time()
                self.ip_index += 1
                if self.ip_index >= len(ips):
                    self.ip_index = 0

            interface, ip = next(islice(ips.items(), self.ip_index, self.ip_index + 1))
            if interface.startswith('eth') or interface.startswith('en'):
                oled.draw_icon(ethernet_icon, 0, 0, scale=1, invert=False,  dither=False, threshold=80)
                oled.draw_text(f'{ip}', 22, 0, size=14, font_path=font)
            elif interface.startswith('wlan') or interface.startswith('wl'):
                oled.draw_icon(wifi_icon, 0, 0, scale=1, invert=False, dither=False, threshold=85)
                oled.draw_text(f'{ip}', 22, 0, size=14, font_path=font)

        # cpu
        oled.draw_icon(cpu_icon, 0, 16, scale=1, invert=False)
        oled.draw_text('CPU', 28, 14, size=10, font_path=font)
        oled.draw_text(f"{cpu_usage}%", 25, 24, size=14, font_path=font)

        # Temp
        oled.draw_icon(temp_icon, 68, 16, scale=1, invert=False)
        oled.draw_text('TEMP', 91, 14, size=10, font_path=font)
        oled.draw_text(f"{int(temp):d}°{temperature_unit}", 89, 24, size=14, font_path=font)

        # RAM
        oled.draw_icon(ram_icon, 0, 40, scale=1, invert=False)
        oled.draw_text('RAM', 28, 38, size=10, font_path=font)
        oled.draw_text(f"{memory_percent}%", 25, 48, size=12, font_path=font)

        oled.display()