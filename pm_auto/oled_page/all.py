from sf_rpi_status import \
    get_cpu_temperature, \
    get_cpu_percent, \
    get_memory_info, \
    get_disks_info, \
    get_ips
import time

from .oled_config import *
from .uilts import *

last_ips = {}
ip_index = 0
ip_show_next_timestamp = 0

def get_data():
    global ip_index

    memory_info = get_memory_info()
    ips = get_ips()

    data = {
        'cpu_temperature': get_cpu_temperature(),
        'cpu_percent': get_cpu_percent(),
        'memory_total': memory_info.total,
        'memory_used': memory_info.used,
        'memory_percent': memory_info.percent,
        'ips': []
    }
    # Get disk info
    disks_info = get_disks_info()
    data['disk_total'] = 0
    data['disk_used'] = 0
    data['disk_percent'] = 0
    data['disk_mounted'] = False
    if disk_mode == 'total':
        for disk in disks_info.values():
            if disk.mounted:
                data['disk_total'] += disk.total
                data['disk_used'] += disk.used
                data['disk_percent'] += disk.percent
                data['disk_mounted'] = True
    else:
        disk = disks_info[disk_mode]
        if disk.mounted:
            data['disk_total'] = disk.total
            data['disk_used'] = disk.used
            data['disk_percent'] = disk.percent
            data['disk_mounted'] = True
        else:
            data['disk_total'] = disk.total
            data['disk_mounted'] = False
    
    # Get IPs
    for interface, ip in ips.items():
        if interface not in last_ips:
            print(f"Connected to {interface}: {ip}")
        elif last_ips[interface] != ip:
            print(f"IP changed for {interface}: {ip}")
        last_ips[interface] = ip
    for interface in last_ips.keys():
        if interface not in ips:
            print(f"Disconnected from {interface}")
            last_ips.pop(interface)

    if len(ips) > 0:
        if ip_interface == 'all':
            data['ips'] = list(ips.values())
        elif ip_interface in ips:
            data['ips'] = [ips[ip_interface]]
            ip_index = 0
        else:
            print(f"Invalid interface: {ip_interface}, available interfaces: {list(ips.keys())}")

    return data

def oled_page_all(oled):
    global ip_index, ip_show_next_timestamp

    data = get_data()

    # Get system status data
    cpu_temp_c = data['cpu_temperature']
    cpu_temp_f = cpu_temp_c * 9 / 5 + 32
    cpu_usage = data['cpu_percent']
    memory_total, memory_unit = format_bytes(data['memory_total'])
    memory_used = format_bytes(data['memory_used'], memory_unit)
    memory_percent = data['memory_percent']
    disk_total, disk_unit = format_bytes(data['disk_total'])
    if data['disk_mounted']:
        disk_used = format_bytes(data['disk_used'], disk_unit)
        disk_percent = data['disk_percent']
    else:
        disk_used = 'NA'
        disk_percent = 0
    ips = data['ips']
    ip = 'DISCONNECTED'

    if len(ips) > 0:
        ip = ips[ip_index]
        if time.time() - ip_show_next_timestamp > IP_SHOW_NEXT_INTERVAL:
            ip_show_next_timestamp = time.time()
            ip_index = (ip_index + 1) % len(ips)

    # Clear draw buffer
    oled.clear()

    # ---- display info ----
    ip_rect =           Rect(39,  0, 88, 10)
    memory_info_rect =  Rect(39, 17, 88, 10)
    memory_rect =       Rect(39, 29, 88, 10)
    disk_info_rect =    Rect(39, 41, 88, 10)
    disk_rect =         Rect(39, 53, 88, 10)

    LEFT_AREA_X = 18
    # cpu usage
    oled.draw_text('CPU', LEFT_AREA_X, 0, align='center')
    oled.draw_pieslice_chart(cpu_usage, LEFT_AREA_X, 27, 15, 180, 0)
    oled.draw_text(f'{cpu_usage} %', LEFT_AREA_X, 27, align='center')
    # cpu temp
    temp = cpu_temp_c if temperature_unit == 'C' else cpu_temp_f
    oled.draw_text(f'{temp:.1f}°{temperature_unit}', LEFT_AREA_X, 37, align='center')
    oled.draw_pieslice_chart(cpu_temp_c, LEFT_AREA_X, 48, 15, 0, 180)
    # RAM
    oled.draw_text(f'RAM:  {memory_used}/{memory_total} {memory_unit}', *memory_info_rect.coord())
    oled.draw_bar_graph_horizontal(memory_percent, *memory_rect.coord(), *memory_rect.size())
    # Disk
    oled.draw_text(f'DISK: {disk_used}/{disk_total} {disk_unit}', *disk_info_rect.coord())
    oled.draw_bar_graph_horizontal(disk_percent, *disk_rect.coord(), *disk_rect.size())
    # IP
    oled.draw.rectangle((ip_rect.x,ip_rect.y,ip_rect.x+ip_rect.width,ip_rect.height), outline=1, fill=1)
    oled.draw_text(ip, *ip_rect.topcenter(), fill=0, align='center')

    # draw the image buffer
    oled.display()