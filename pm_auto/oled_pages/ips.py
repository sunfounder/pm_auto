from itertools import islice
import time

from sf_rpi_status import get_ips

from pathlib import Path
grandparent_dir = Path(__file__).resolve().parent.parent
ethernet_icon = str(grandparent_dir) + '/icons/ethernet_icon_20.png'
wifi_icon = str(grandparent_dir) + '/icons/wifi_icon_20.png'
net_icon = str(grandparent_dir) + '/icons/net_icon_20.png'
error = str(grandparent_dir) + '/icons/error_icon_20.png'

ip_index = 0
ip_num = 0
cycle_time_start = 0

def oled_page_ips(oled, config):
    global ip_index, ip_num, cycle_time_start

    scroll_interval = config['scroll_interval']

    ips = get_ips()
    
    oled.clear()

    if len(ips) == 0:
        oled.draw_icon(error, 53, 0, scale=1, invert=False, dither=False, threshold=50)
        oled.draw_text('DISCONNECTED', 14, 22, size=14)
    else:
        if ip_num != len(ips):
            ip_index = 0
            cycle_time_start = time.time()
            ip_num = len(ips)

        if time.time() - cycle_time_start >= scroll_interval:
            cycle_time_start = time.time()
            ip_index += 3
            if ip_index >= len(ips):
                ip_index = 0

        _iter = islice(ips.items(), ip_index, ip_index + 3)

        for i in range(3):
            try:
                interface, ip = next(_iter)
                if interface.startswith('eth') or interface.startswith('en'):
                    oled.draw_icon(ethernet_icon, 0, i*22, scale=1, invert=False,  dither=False, threshold=80)
                    oled.draw_text(f'{ip}', 22, i * 22, size=14)
                elif interface.startswith('wlan') or interface.startswith('wl'):
                    oled.draw_icon(wifi_icon, 0, i*22, scale=1, invert=False, dither=False, threshold=85)
                    oled.draw_text(f'{ip}', 22, i * 22, size=14)
            except StopIteration:
                break

    oled.display()
