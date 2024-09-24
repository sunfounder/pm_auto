import time
import threading
import logging
from sf_rpi_status import \
    get_cpu_temperature, \
    get_cpu_percent, \
    get_memory_info, \
    get_disk_info, \
    get_disks_info, \
    get_ips, \
    shutdown

from .utils import format_bytes, has_common_items, log_error

from .fan_control import FanControl, FANS

app_name = 'pm_auto'

DEFAULT_CONFIG = {
    'rgb_led_count': 4,
    'rgb_enable': True,
    'rgb_color': '#ff00ff',
    'rgb_brightness': 100,
    'rgb_style': 'rainbow',
    'rgb_speed': 0,
    'oled_enable': True,
    'oled_rotation': 0,
    'oled_disk': 'total',  # 'total' or the name of the disk, normally 'mmcblk0' for SD Card, 'nvme0n1' for NVMe SSD
    'oled_network_interface': 'all',  # 'all' or the name of the interface, normally 'wlan0' for WiFi, 'eth0' for Ethernet
    'temperature_unit': 'C',
    'gpio_fan_mode': 1,
    'gpio_fan_led_pin': 5,
    "gpio_fan_pin": 6,
    "interval": 1,
}

class PMAuto():
    @log_error
    def __init__(self, config=DEFAULT_CONFIG, peripherals=[], get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False
        self.peripherals = peripherals

        self.oled = None
        self.ws2812 = None
        self.fan = None
        self.spc = None
        if 'oled' in peripherals:
            self.log.debug("Initializing OLED")
            self.oled = OLEDAuto(config, get_logger=get_logger)
            if not self.oled.is_ready():
                self.log.error("Failed to initialize OLED")
            else:
                self.log.debug("OLED initialized")            
        if 'ws2812' in peripherals:
            from .ws2812 import WS2812  
            self.ws2812 = WS2812(config, get_logger=get_logger)
            if not self.ws2812.is_ready():
                self.log.error("Failed to initialize WS2812")
            else:
                self.log.debug("WS2812 initialized")
                self.ws2812.start()
        # if FANS in peripherals:
        if self.fan_enabled() or 'spc' in peripherals:
            self.fan = FanControl(config, fans=peripherals, get_logger=get_logger)
        if 'spc' in peripherals:
            self.spc = SPCAuto(get_logger=get_logger)

        self.interval = 1
    
        self.thread = None
        self.running = False

        self.update_config(config)
        self.__on_state_changed__ = None
    
    def fan_enabled(self):
        return has_common_items(FANS, self.peripherals)

    @log_error
    def set_debug_level(self, level):
        self.log.setLevel(level)
        if self.oled is not None:
            self.oled.set_debug_level(level)
        if self.ws2812 is not None:
            self.ws2812.set_debug_level(level)
        if self.fan is not None:
            self.fan.set_debug_level(level)
        if self.spc is not None:
            self.spc.set_debug_level(level)

    @log_error
    def set_on_state_changed(self, callback):
        self.__on_state_changed__ = callback
        self.fan.set_on_state_changed(callback)

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def update_config(self, config):
        self.log.debug(f"Update config: {config}")
        if 'interval' in config:
            if not isinstance(config['interval'], (int, float)):
                self.log.error("Invalid interval")
                return
            self.log.info("Interval set to %d", config['interval'])
            self.interval = config['interval']
        if 'oled' in self.peripherals:
            self.oled.update_config(config)
        if 'ws2812' in self.peripherals:
            self.ws2812.update_config(config)
        if self.fan_enabled():
            self.fan.update_config(config)

    @log_error
    def loop(self):
        while self.running:
            if self.oled is not None and self.oled.is_ready():
                self.oled.run()
            if self.fan is not None:
                self.fan.run()
            if self.spc is not None and self.spc.is_ready():
                self.spc.run()
            time.sleep(self.interval)

    @log_error
    def start(self):
        if self.running:
            self.log.warning("Already running")
            return
        self.running = True
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()
        self.log.info("PM Auto Start")


    @log_error
    def stop(self):
        if self.running:
            self.thread.join()
        self.running = False
        if self.oled is not None and self.oled.is_ready():
            self.oled.close()
        if self.ws2812 is not None and self.ws2812.is_ready():
            self.ws2812.stop()
        if self.fan is not None:
            self.fan.close()
        self.log.info("PM Auto Stop")

OLED_DEFAULT_CONFIG = {
    'temperature_unit': 'C',
    'oled_enable': True,
    'oled_rotation': 0,
    'oled_disk': 'total',  # 'total' or the name of the disk, normally 'mmcblk0' for SD Card, 'nvme0n1' for NVMe SSD
    'oled_network_interface': 'all',  # 'all' or the name of the interface, normally 'wlan0' for WiFi, 'eth0' for Ethernet
}

class OLEDAuto():
    @log_error
    def __init__(self, config, get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False

        from .oled import OLED, Rect
        self.oled = OLED(get_logger=get_logger)
        self.Rect = Rect
        if not self.oled.is_ready():
            self.log.error("Failed to initialize OLED")
            return
        self._is_ready = self.oled.is_ready()

        self.last_ip = ''
        self.ip_index = 0
        self.ip_show_next_timestamp = 0
        self.ip_show_next_interval = 3
        self.temperature_unit = OLED_DEFAULT_CONFIG['temperature_unit']
        self.oled_enable = OLED_DEFAULT_CONFIG['oled_enable']
        self.oled_disk = OLED_DEFAULT_CONFIG['oled_disk']
        self.ip_interface = OLED_DEFAULT_CONFIG['oled_network_interface']
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
        if "oled_enable" in config:
            self.log.debug(f"Update oled_enable to {config['oled_enable']}")
            self.oled_enable = config['oled_enable']
        if "oled_rotation" in config:
            self.log.debug(f"Update oled_rotation to {config['oled_rotation']}")
            self.set_rotation(config['oled_rotation'])
        if "oled_disk" in config:
            self.log.debug(f"Update oled_disk to {config['oled_disk']}")
            self.oled_disk = config['oled_disk']
        if "oled_network_interface" in config:
            self.log.debug(f"Update oled_network_interface to {config['oled_network_interface']}")
            self.ip_interface = config['ip_interface']

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
        }
        # Get disk info
        disks_info = get_disks_info()
        data['disk_total'] = 0
        data['disk_used'] = 0
        data['disk_percent'] = 0
        data['disk_mounted'] = False
        if self.oled_disk == 'total':
            for disk in disks_info.values():
                if disk.mounted:
                    data['disk_total'] += disk.total
                    data['disk_used'] += disk.used
                    data['disk_percent'] += disk.percent
                    data['disk_mounted'] = True
        else:
            disk = disks_info[self.oled_disk]
            if disk.mounted:
                data['disk_total'] = disk.total
                data['disk_used'] = disk.used
                data['disk_percent'] = disk.percent
                data['disk_mounted'] = True
            else:
                data['disk_total'] = disk.total
                data['disk_mounted'] = False
                
        
        # Get IPs
        if self.ip_interface == 'all':
            data['ips'] = list(ips.values())
        elif self.ip_interface in ips:
            data['ips'] = [ips[self.ip_interface]]
        else:
            self.log.error(f"Invalid ip_interface: {self.ip_interface}, available ips: {ips.keys()}")

        return data

    @log_error
    def handle_oled(self, data):
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
            ip = ips[self.ip_index]
            if time.time() - self.ip_show_next_timestamp > self.ip_show_next_interval:
                self.ip_show_next_timestamp = time.time()
                self.ip_index = (self.ip_index + 1) % len(ips)

        # Clear draw buffer
        self.oled.clear()

        # ---- display info ----
        ip_rect =           self.Rect(39,  0, 88, 10)
        memory_info_rect =  self.Rect(39, 17, 88, 10)
        memory_rect =       self.Rect(39, 29, 88, 10)
        disk_info_rect =    self.Rect(39, 41, 88, 10)
        disk_rect =         self.Rect(39, 53, 88, 10)

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
        self.oled.display()

    @log_error
    def run(self):
        if self.oled is None or not self.oled.is_ready() or not self.oled_enable:
            # Clear draw buffer
            self.oled.clear()
            # draw the image buffer
            self.oled.display()
            return

        data = self.get_data()
        self.handle_oled(data)

    @log_error
    def close(self):
        if self.oled is not None and self.oled.is_ready():
            self.oled.clear()
            self.oled.display()
            self.oled.off()
            self.log.debug("OLED Close")

class SPCAuto():
    @log_error
    def __init__(self, get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False

        from spc.spc import SPC
        self.spc = SPC(get_logger=get_logger)
        if not self.spc.is_ready():
            self._is_ready = False
            return

        self._is_ready = True
        self.shutdown_request = 0
        self.is_plugged_in = False

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def handle_shutdown(self):
        if self.spc is None or not self.spc.is_ready():
            return

        shutdown_request = self.spc.read_shutdown_request()
        if shutdown_request != self.shutdown_request:
            self.shutdown_request = shutdown_request
            self.log.debug(f"Shutdown request: {shutdown_request}")
        if shutdown_request in self.spc.SHUTDOWN_REQUESTS:
            if shutdown_request == self.spc.SHUTDOWN_REQUEST_LOW_POWER:
                self.log.info('Low power shutdown.')
            elif shutdown_request == self.spc.SHUTDOWN_REQUEST_BUTTON:
                self.log.info('Button shutdown.')
            shutdown()

    @log_error
    def handle_external_input(self):
        if self.spc is None or not self.spc.is_ready():
            return

        if 'external_input' not in self.spc.device.peripherals:
            return

        if 'battery' not in self.spc.device.peripherals:
            return

        is_plugged_in = self.spc.read_is_plugged_in()
        if is_plugged_in != self.is_plugged_in:
            self.is_plugged_in = is_plugged_in
            if is_plugged_in == True:
                self.log.info(f"External input plug in")
            else:
                self.log.info(f"External input unplugged")
        if is_plugged_in == False:
            shutdown_pct = self.spc.read_shutdown_battery_pct()
            current_pct= self.spc.read_battery_percentage()
            if current_pct < shutdown_pct:
                self.log.info(f"Battery is below {shutdown_pct}, shutdown!", level="INFO")
                shutdown()

    @log_error
    def run(self):
        self.handle_external_input()
        self.handle_shutdown()
