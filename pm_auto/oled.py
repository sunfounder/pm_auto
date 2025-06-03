from .ssd1306 import SSD1306, Rect
from sf_rpi_status import \
    get_cpu_temperature, \
    get_cpu_percent, \
    get_memory_info, \
    get_disks_info, \
    get_ips

from .utils import format_bytes, log_error, DebounceRunner
import time

OLED_DEFAULT_CONFIG = {
    'temperature_unit': 'C',
    'oled_enable': True,
    'oled_rotation': 0,
    'oled_disk': 'total',  # 'total' or the name of the disk, normally 'mmcblk0' for SD Card, 'nvme0n1' for NVMe SSD
    'oled_network_interface': 'all',  # 'all' or the name of the interface, normally 'wlan0' for WiFi, 'eth0' for Ethernet
    'oled_sleep_timeout': 0,
}

class OLED():
    @log_error
    def __init__(self, config, get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False

        self.oled = SSD1306(get_logger=get_logger)
        if not self.oled.is_ready():
            self.log.error("Failed to initialize OLED")
            return
        self._is_ready = self.oled.is_ready()

        self.temperature_unit = OLED_DEFAULT_CONFIG['temperature_unit']
        self.disk_mode = OLED_DEFAULT_CONFIG['oled_disk']
        self.ip_interface = OLED_DEFAULT_CONFIG['oled_network_interface']
        self.sleep_timeout = OLED_DEFAULT_CONFIG['oled_sleep_timeout']
        self.enable = OLED_DEFAULT_CONFIG['oled_enable']
        self.ip_index = 0
        self.ip_show_next_timestamp = 0
        self.ip_show_next_interval = 3
        self.wake_flag = True
        self.wake_start_time = 0
        self.last_ips = {}
        self.debounce_display = DebounceRunner(self.oled.display, 0.5)
        
        self.update_config(config)

    @log_error
    def set_debug_level(self, level):
        self.log.setLevel(level)

    @log_error
    def update_config(self, config):
        if "temperature_unit" in config:
            if config['temperature_unit'] not in ['C', 'F']:
                self.log.error("Invalid temperature unit")
                return
            self.log.debug(f"Update temperature_unit to {config['temperature_unit']}")
            self.temperature_unit = config['temperature_unit']
        if "oled_rotation" in config:
            self.log.debug(f"Update oled_rotation to {config['oled_rotation']}")
            self.set_rotation(config['oled_rotation'])
        if "oled_disk" in config:
            self.log.debug(f"Update oled_disk to {config['oled_disk']}")
            self.disk_mode = config['oled_disk']
        if "oled_network_interface" in config:
            self.log.debug(f"Update oled_network_interface to {config['oled_network_interface']}")
            self.ip_interface = config['oled_network_interface']
        if "oled_sleep_timeout" in config:
            self.log.debug(f"Update oled_sleep_timeout to {config['oled_sleep_timeout']}")
            self.sleep_timeout = config['oled_sleep_timeout']
        if "oled_enable" in config:
            self.log.debug(f"Update oled_enable to {config['oled_enable']}")
            self.enable = config['oled_enable']
            if self.enable:
                self.wake()
            else:
                self.sleep()

    @log_error
    def set_rotation(self, rotation):
        self.oled.set_rotation(rotation)

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def get_data(self):
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
        if self.disk_mode == 'total':
            for disk in disks_info.values():
                if disk.mounted:
                    data['disk_total'] += disk.total
                    data['disk_used'] += disk.used
                    data['disk_percent'] += disk.percent
                    data['disk_mounted'] = True
        else:
            disk = disks_info[self.disk_mode]
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
            if interface not in self.last_ips:
                self.log.info(f"Connected to {interface}: {ip}")
            elif self.last_ips[interface] != ip:
                self.log.info(f"IP changed for {interface}: {ip}")
            self.last_ips[interface] = ip
        for interface in self.last_ips.keys():
            if interface not in ips:
                self.log.info(f"Disconnected from {interface}")
                self.last_ips.pop(interface)

        if len(ips) > 0:
            if self.ip_interface == 'all':
                data['ips'] = list(ips.values())
            elif self.ip_interface in ips:
                data['ips'] = [ips[self.ip_interface]]
                self.ip_index = 0
            else:
                self.log.warning(f"Invalid interface: {self.ip_interface}, available interfaces: {list(ips.keys())}")

        return data

    @log_error
    def draw_oled(self):
        data = self.get_data()
        # Get system status data
        cpu_temp_c = data['cpu_temperature']
        cpu_temp_f = cpu_temp_c * 9 / 5 + 32
        cpu_usage = data['cpu_percent']
        memory_total, memory_unit = format_bytes(data['memory_total'], auto_threshold=100)
        memory_used = format_bytes(data['memory_used'], memory_unit)
        memory_percent = data['memory_percent']
        disk_total, disk_unit = format_bytes(data['disk_total'], auto_threshold=100)
        if data['disk_mounted']:
            disk_used = format_bytes(data['disk_used'], disk_unit)
            disk_percent = data['disk_percent']
        else:
            disk_used = 'NA'
            disk_percent = 0
        ips = data['ips']
        ip = 'DISCONNECTED'

        if len(ips) > 0:
            ip = ips[self.ip_index]
            if time.time() - self.ip_show_next_timestamp > self.ip_show_next_interval:
                self.ip_show_next_timestamp = time.time()
                self.ip_index = (self.ip_index + 1) % len(ips)

        # Clear draw buffer
        self.oled.clear()

        # ---- display info ----
        ip_rect =           Rect(39,  0, 88, 10)
        memory_info_rect =  Rect(39, 17, 88, 10)
        memory_rect =       Rect(39, 29, 88, 10)
        disk_info_rect =    Rect(39, 41, 88, 10)
        disk_rect =         Rect(39, 53, 88, 10)

        LEFT_AREA_X = 18
        # cpu usage
        self.oled.draw_text('CPU', LEFT_AREA_X, 0, align='center')
        self.oled.draw_pieslice_chart(cpu_usage, LEFT_AREA_X, 27, 15, 180, 0)
        self.oled.draw_text(f'{cpu_usage} %', LEFT_AREA_X, 27, align='center')
        # cpu temp
        temp = cpu_temp_c if self.temperature_unit == 'C' else cpu_temp_f
        self.oled.draw_text(f'{temp:.1f}°{self.temperature_unit}', LEFT_AREA_X, 37, align='center')
        self.oled.draw_pieslice_chart(cpu_temp_c, LEFT_AREA_X, 48, 15, 0, 180)
        # RAM
        self.oled.draw_text(f'RAM:  {memory_used}/{memory_total} {memory_unit}', *memory_info_rect.coord())
        self.oled.draw_bar_graph_horizontal(memory_percent, *memory_rect.coord(), *memory_rect.size())
        # Disk
        self.oled.draw_text(f'DISK: {disk_used}/{disk_total} {disk_unit}', *disk_info_rect.coord())
        self.oled.draw_bar_graph_horizontal(disk_percent, *disk_rect.coord(), *disk_rect.size())
        # IP
        self.oled.draw.rectangle((ip_rect.x,ip_rect.y,ip_rect.x+ip_rect.width,ip_rect.height), outline=1, fill=1)
        self.oled.draw_text(ip, *ip_rect.topcenter(), fill=0, align='center')

        # draw the image buffer
        self.debounce_display()

    @log_error
    def wake(self):
        if self.oled is None or not self.oled.is_ready() or self.enable == False:
            return
        self.log.debug("OLED wake up")
        self.wake_start_time = time.time()
        if self.wake_flag != True:
            self.wake_flag = True
            self.draw_oled()

    @log_error
    def sleep(self):
        self.wake_flag = False
        self.oled.clear()
        self.oled.display()

    @log_error
    def run(self):
        if self.oled is None or not self.oled.is_ready() or self.wake_flag == False or self.enable == False:
            return

        if self.sleep_timeout > 0 and time.time() - self.wake_start_time > self.sleep_timeout and self.wake_flag == True:
            self.log.info("OLED sleep timeout, sleeping")
            self.sleep()
            return

        self.draw_oled()

    @log_error
    def close(self):
        if self.oled is not None and self.oled.is_ready():
            self.oled.clear()
            self.oled.display()
            self.oled.off()
            self.log.debug("OLED closed")

