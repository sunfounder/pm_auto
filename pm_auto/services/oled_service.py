from pm_auto.services.pironman_mcu_service import INTERVAL
from ..libs.ssd1306 import SSD1306, Rect
from sf_rpi_status import \
    get_cpu_temperature, \
    get_cpu_percent, \
    get_memory_info, \
    get_disks_info, \
    get_ips
from ..libs.i2c import I2C
from ..libs.utils import format_bytes, log_error

import time
import threading
from enum import Enum

INTERVAL = 1

OLED_DEFAULT_CONFIG = {
    'temperature_unit': 'C',
    'oled_enable': True,
    'oled_rotation': 0,
    'oled_disk': 'total',  # 'total' or the name of the disk, normally 'mmcblk0' for SD Card, 'nvme0n1' for NVMe SSD
    'oled_network_interface': 'all',  # 'all' or the name of the interface, normally 'wlan0' for WiFi, 'eth0' for Ethernet
    'oled_sleep_timeout': 5,
}

class OLEDService():
    @log_error
    def __init__(self, config, get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False

        try:
            self.oled = SSD1306()
        except Exception as e:
            self.log.error(f"Failed to initialize OLED service: {e}")
            return
        self._is_ready = self.oled.is_ready()

        self.temperature_unit = OLED_DEFAULT_CONFIG['temperature_unit']
        self.disk_mode = OLED_DEFAULT_CONFIG['oled_disk']
        self.ip_interface = OLED_DEFAULT_CONFIG['oled_network_interface']
        self.sleep_timeout = OLED_DEFAULT_CONFIG['oled_sleep_timeout']
        self.enable = OLED_DEFAULT_CONFIG['oled_enable']
        self.wake_flag = True
        self.button = False
        self.wake_start_time = 0
        self.is_power_off = False
        self.running = False
        self.thread = None
        
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
            if config['oled_enable']:
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
    def show_shutdown_screen(self, reason):
        self.log.info(f"Shutdown reason: {reason}")
        self.is_power_off = True
        self.wake()

    @log_error
    def wake(self):
        self.wake_start_time = time.time()
        self.wake_flag = True

    def set_button(self, button_state):
        self.button = button_state

    @log_error
    def sleep(self):
        self.wake_flag = False
        self.oled.clear()
        self.oled.display()

    @log_error
    def loop(self):
        from ..oled_page.ips import oled_page_ips
        from ..oled_page.disk import oled_page_disk
        from ..oled_page.performance import oled_page_performance
        from ..oled_page.power_off import oled_page_power_off

        page = [
            oled_page_performance,
            oled_page_ips,
            oled_page_disk,
            ]
    
        page_index = 0
        last_page_index = -1
        last_refresh_time = 0

        if self.oled is None or not self.oled.is_ready():
            self.log.error("OLED service not ready")
            return

        while self.running:

            if self.is_power_off == True:
                oled_page_power_off(self.oled)
                time.sleep(.5)
                continue

            if self.button == 'single_click':
                if not self.wake_flag:
                    self.log.info("OLED service waking up")
                    self.wake_flag = True
                    last_page_index = -1
                else:
                    page_index += 1
                    if page_index >= len(page):
                        page_index = 0
                self.wake_start_time = time.time()
            elif self.button == 'double_click':
                if self.wake_flag:
                    page_index -= 1
                    if page_index < 0:
                        page_index = len(page) - 1
                    self.wake_start_time = time.time()
                    
            if self.wake_flag:
                if last_page_index != page_index or time.time() - last_refresh_time > INTERVAL:
                    last_page_index = page_index
                    last_refresh_time = time.time()
                    page[page_index](self.oled)

                if self.sleep_timeout > 0 and time.time() - self.wake_start_time > self.sleep_timeout:
                    self.log.info("OLED sleep timeout, sleeping")
                    self.sleep()
                    continue

            time.sleep(.05)

    @log_error
    def start(self):
        if self.running:
            self.log.warning("OLED service already running")
            return
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    @log_error
    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
        if self.oled is not None and self.oled.is_ready():
            self.oled.clear()
            self.oled.display()
            self.oled.off()
            self.log.debug("OLED service closed")

