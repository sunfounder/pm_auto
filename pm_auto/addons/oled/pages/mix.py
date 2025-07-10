from itertools import islice
import time

from pm_auto.libs.utils import get_icon, get_font

font = get_font('UbuntuSans-Regular.ttf')

ethernet_icon = get_icon('icon_lan_20.png')
wifi_icon = get_icon('icon_wifi_20.png')
net_icon = get_icon('icon_network_20.png')
cpu_icon = get_icon('icon_cpu_24.png')
temp_icon = get_icon('icon_temperature_24.png')
ram_icon = get_icon('icon_ram_24.png')
error_icon = get_icon('icon_error_20.png')

ip_index = 0
ip_num = 0
cycle_time_start = 0

def oled_page_mix(oled, data, config):
    global ip_index, ip_num, cycle_time_start

    scroll_interval = config['scroll_interval']
    temperature_unit = config['temperature_unit']

    ips = data.get('ips', [])

    cpu_temp_c = data.get("cpu_temperature", 0)
    cpu_temp_f = cpu_temp_c * 9 / 5 + 32
    cpu_usage = data.get("cpu_usage", 0)
    if cpu_usage >= 100:
        cpu_usage = 100

    temp = cpu_temp_c if temperature_unit == 'C' else cpu_temp_f
    temp = round(temp, 1)

    oled.clear()

    # ips
    if len(ips) == 0:
        oled.draw_icon(error_icon, 0, 0, scale=1, invert=False, dither=False, threshold=50)
        oled.draw_text('DISCONNECTED', 22, 0, size=14, font_path=font)
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
            oled.draw_text(f'{ip}', 22, 0, size=14, font_path=font)
        elif interface.startswith('wlan') or interface.startswith('wl'):
            oled.draw_icon(wifi_icon, 0, 0, scale=1, invert=False, dither=False, threshold=85)
            oled.draw_text(f'{ip}', 22, 0, size=14, font_path=font)

    # cpu
    oled.draw_icon(cpu_icon, 0, 25, scale=1, invert=False)
    oled.draw_text('CPU', 28, 25, size=10, font_path=font)
    oled.draw_text(f"{cpu_usage}%", 25, 35, size=14, font_path=font)

    # Temp
    oled.draw_icon(temp_icon, 68, 25, scale=1, invert=False)
    oled.draw_text('TEMP', 91, 25, size=10, font_path=font)
    oled.draw_text(f"{int(temp):d}°{temperature_unit}", 89, 35, size=14, font_path=font)

    oled.display()