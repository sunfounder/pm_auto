from sf_rpi_status import \
    get_cpu_temperature, \
    get_cpu_percent, \
    get_memory_info, \
    get_disks_info, \
    get_ips
import time

from.oled_config import *


from pathlib import Path
grandparent_dir = Path(__file__).resolve().parent.parent
ethernet_icon = str(grandparent_dir) + '/icons/ethernet_icon_20.png'
wifi_icon = str(grandparent_dir) + '/icons/wifi_icon_20.png'
net_icon = str(grandparent_dir) + '/icons/net_icon_20.png'

def oled_page_ips(oled):
    ips = get_ips()
    ips['lo'] = '127.0.0.1'
    oled.clear()

    i = 0
    for interface, ip in ips.items():
        if interface == 'eth0':
            oled.draw_icon(ethernet_icon, 0, i*22, scale=1, invert=False,  dither=False, threshold=80)
        elif interface == 'wlan0':
            oled.draw_icon(wifi_icon, 0, i*22, scale=1, invert=False, dither=False, threshold=85)
        else:
            oled.draw_icon(net_icon, 0, i*22, scale=1, invert=False, dither=False, threshold=100)

        oled.draw_text(f'{ip}', 22, i * 22, size=14)
        i += 1

    oled.display()
