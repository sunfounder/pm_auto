from sf_rpi_status import get_disks_info, get_disk_temperature
from .oled_config import *
from .uilts import *


from importlib.resources import files as resource_files
__package_name__ = __name__.split('.')[0]
sdcard_icon = str(resource_files(__package_name__).joinpath('icons/sdcard_icon_20.png'))
nvme_icon = str(resource_files(__package_name__).joinpath('icons/nvme_icon_20.png'))
usb_stick_icon = str(resource_files(__package_name__).joinpath('icons/usb_stick_icon_20.png'))
disk_icon = str(resource_files(__package_name__).joinpath('icons/disk_icon_20.png'))
raid_icon = str(resource_files(__package_name__).joinpath('icons/raid_icon_20.png'))


def oled_page_disk(oled):
    disks_info = get_disks_info() # temperature=True
    # print(disks_info)
    oled.clear()


    # i = 0
    # for name, info in disks_info.items():
    #     # 是否包含
    #     if 'mmcblk' in name:
    #         oled.draw_icon(sdcard_icon, 0, i * 22)
    #     elif 'nvme0' in name:
    #         oled.draw_icon(nvme_icon, 0, i * 22+4)
    #         oled.draw_text(f'ssd0', 0, i * 22, size=8)
    #     elif 'nvme1' in name:
    #         oled.draw_icon(nvme_icon, 0, i * 22+4)
    #         oled.draw_text(f'ssd1', 0, i * 22, size=8)
    #     elif '/dev/sd' in name:
    #         oled.draw_icon(disk_icon, 0, i * 22)
    #     elif '/dev/md' in name:
    #         oled.draw_icon(raid_icon, 0, i * 22)
    #     else:
    #         oled.draw_icon(usb_stick_icon, 0, i * 22)

    #     # print(get_disk_temperature(name))

    #     _total, _uint = format_bytes(info.total)
    #     _used = format_bytes(info._used, _uint)
    #     oled.draw_text(f'{_used}/{_total} {_uint}', 32, i * 22, size=12)
    #     oled.draw_bar_graph_horizontal(info._percent, 26, i * 23 + 12, 100, 5)
    #     i += 1


    
    i = 0
    devices = disks_info.keys()

    for name in devices:
        if 'mmcblk' in name:
            oled.draw_icon(sdcard_icon, 0, i * 22)
            info = disks_info[name]
            _total, _uint = format_bytes(info.total)
            _used = format_bytes(info._used, _uint)
            oled.draw_text(f'{_used}/{_total} {_uint}', 32, i * 22, size=12)
            oled.draw_bar_graph_horizontal(info._percent, 26, i * 23 + 12, 100, 5)
            disks_info.pop(name)
            i += 1
            break
    for name in devices:
        if '/dev/md' in name:
            oled.draw_icon(raid_icon, 0, i * 22)
            info = disks_info[name]
            _total, _uint = format_bytes(info.total)
            _used = format_bytes(info._used, _uint)
            oled.draw_text(f'{_used}/{_total} {_uint}', 32, i * 22, size=12)
            oled.draw_bar_graph_horizontal(info._percent, 26, i * 23 + 12, 100, 5)
            disks_info.pop(name)
            i += 1
            break

    for name, info in disks_info.items():
        if 'nvme0' in name:
            oled.draw_icon(nvme_icon, 0, i * 22+4)
            oled.draw_text(f'ssd0', 0, i * 22, size=8)
        elif 'nvme1' in name:
            oled.draw_icon(nvme_icon, 0, i * 22+4)
            oled.draw_text(f'ssd1', 0, i * 22, size=8)
        elif '/dev/sd' in name:
            oled.draw_icon(disk_icon, 0, i * 22)
        else:
            oled.draw_icon(usb_stick_icon, 0, i * 22)

        # print(get_disk_temperature(name))

        _total, _uint = format_bytes(info.total)
        _used = format_bytes(info._used, _uint)
        oled.draw_text(f'{_used}/{_total} {_uint}', 32, i * 22, size=12)
        oled.draw_bar_graph_horizontal(info._percent, 26, i * 23 + 12, 100, 5)
        i += 1

    oled.display()
    