from itertools import islice
import time

from sf_rpi_status import \
    get_cpu_temperature, \
    get_cpu_percent, \
    get_ips

from pathlib import Path
grandparent_dir = Path(__file__).resolve().parent.parent
ethernet_icon = str(grandparent_dir) + '/icons/ethernet_icon_20.png'
wifi_icon = str(grandparent_dir) + '/icons/wifi_icon_20.png'
net_icon = str(grandparent_dir) + '/icons/net_icon_20.png'
cpu_icon = str(grandparent_dir) + '/icons/cpu_icon_24.png'
temp_icon = str(grandparent_dir) + '/icons/temperature_icon_24.png'
ram_icon = str(grandparent_dir) + '/icons/ram_icon_24.png'
error = str(grandparent_dir) + '/icons/error_icon_20.png'

ip_index = 0
ip_num = 0
cycle_time_start = 0

def oled_page_mix(oled, config):
    global ip_index, ip_num, cycle_time_start

    scroll_interval = config['scroll_interval']
    temperature_unit = config['temperature_unit']

    ips = get_ips()

    cpu_temp_c = get_cpu_temperature()
    cpu_temp_f = cpu_temp_c * 9 / 5 + 32
    cpu_usage = get_cpu_percent()
    if cpu_usage >= 100:
        cpu_usage = 100

    temp = cpu_temp_c if temperature_unit == 'C' else cpu_temp_f
    temp = round(temp, 1)

    oled.clear()

    # ips
    if len(ips) == 0:
        oled.draw_icon(error, 0, 0, scale=1, invert=False, dither=False, threshold=50)
        oled.draw_text('DISCONNECTED', 22, 0, size=14)
    else:
        if ip_num != len(ips):
            ip_index = 0
            cycle_time_start = time.time()
            ip_num = len(ips)
    
        if time.time() - cycle_time_start >= scroll_interval:
            cycle_time_start = time.time()
            ip_index += 1
            if ip_index >= len(ips):
                ip_index = 0

        interface, ip = next(islice(ips.items(), ip_index, ip_index + 1))
        if interface.startswith('eth') or interface.startswith('en'):
            oled.draw_icon(ethernet_icon, 0, 0, scale=1, invert=False,  dither=False, threshold=80)
            oled.draw_text(f'{ip}', 22, 0, size=14)
        elif interface.startswith('wlan') or interface.startswith('wl'):
            oled.draw_icon(wifi_icon, 0, 0, scale=1, invert=False, dither=False, threshold=85)
            oled.draw_text(f'{ip}', 22, 0, size=14)

    # cpu
    oled.draw_icon(cpu_icon, 0, 25, scale=1, invert=False)
    oled.draw_text('CPU', 28, 25, size=10)
    oled.draw_text(f"{cpu_usage}%", 25, 35, size=14)

    # Temp
    oled.draw_icon(temp_icon, 68, 25, scale=1, invert=False)
    oled.draw_text('TEMP', 91, 25, size=10)
    oled.draw_text(f"{int(temp):d}°{temperature_unit}", 89, 35, size=14)

    oled.display()