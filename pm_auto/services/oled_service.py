from pm_auto.services.pironman_mcu_service import INTERVAL
from ..libs.ssd1306 import SSD1306
from ..libs.utils import log_error

import logging
import time
import threading

OLED_DEFAULT_CONFIG = {
    'oled_enable': True,
    'oled_rotation': 0, # 0, 90, 180, 270 degrees
    'scroll_interval': 3,  # seconds, how often to scroll the content
    'oled_sleep_timeout': 10, # seconds, how long to wait before going to sleep
    'temperature_unit': 'C', # 'C' for Celsius, 'F' for Fahrenheit
    'oled_pages': [
        'mix',
        'performance',
        'ips',
        'disk',
    ]
}
class OLEDService():
    REFRESH_INTERVAL = 1 # seconds, how often to refresh the display
    MIN_SLEEP_TIMEOUT = 5 # 5s, minimum sleep timeout
    MAX_SLEEP_TIMEOUT = 3600 # 600s, 10min, maximum sleep timeout

    @log_error
    def __init__(self, config, log=None):
        self.log = log or logging.getLogger(__name__)
        self._is_ready = False

        try:
            self.oled = SSD1306()
        except Exception as e:
            self.log.error(f"Failed to initialize OLED service: {e}")
            return
        self._is_ready = self.oled.is_ready()

        self.config = OLED_DEFAULT_CONFIG.copy()
        self.update_config(config)

        self.enable = self.config['oled_enable']
        self.rotation = self.config['oled_rotation']
        self.sleep_timeout = self.config['oled_sleep_timeout']
        self.oled_pages = self.config['oled_pages']

        self.wake_flag = True
        self.button = False
        self.wake_start_time = 0
        self.is_power_off = False
        self.running = False
        self.thread = None

    @log_error
    def update_config(self, config):
        if "oled_enable" in config:
            _enable = bool(config['oled_enable'])
            self.config['oled_enable'] = _enable
            self.log.debug(f"Update oled_enable to {_enable}")
            if _enable:
                self.wake()
            else:
                self.sleep()
        if "oled_rotation" in config:
            _rotation = int(config['oled_rotation'])
            if _rotation not in [0, 90, 180, 270]:
                self.log.error("Invalid rotation value, must be 0, 90, 180, or 270")
            else:
                self.config['oled_rotation'] = _rotation
                self.set_rotation(_rotation)
                self.log.debug(f"Update oled_rotation to {_rotation}")
        if "scroll_interval" in config:
            self.config['scroll_interval'] = config['scroll_interval']
            self.log.debug(f"Update scroll_interval to {config['scroll_interval']}")
        if "oled_sleep_timeout" in config:
            _timeout = int(config['oled_sleep_timeout'])
            if _timeout < self.MIN_SLEEP_TIMEOUT or _timeout > self.MAX_SLEEP_TIMEOUT:
                self.log.error(f"Invalid sleep timeout value, must be between {self.MIN_SLEEP_TIMEOUT} and {self.MAX_SLEEP_TIMEOUT}")
            else:
                self.config['oled_sleep_timeout'] = _timeout
                self.log.debug(f"Update oled_sleep_timeout to {_timeout}")
        if "temperature_unit" in config:
            _unit = config['temperature_unit']
            if _unit not in ['C', 'F']:
                self.log.error("Invalid temperature unit, must be 'C' or 'F'")
            else:
                self.config['temperature_unit'] = _unit
                self.log.debug(f"Update temperature_unit to {_unit}")
        if "oled_pages" in config:
            self.config['oled_pages'] = config['oled_pages']
            self.log.debug(f"Update oled_pages to {config['oled_pages']}")

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
    def init_pages(self):
        pages = []
        for page_name in self.oled_pages:
            if page_name ==  'performance':
                try:
                    from ..oled_pages.performance import oled_page_performance
                    pages.append(oled_page_performance)
                except Exception as e:
                    self.log.error(f"Failed to import oled_page_performance: {e}")
            elif page_name == 'ips':
                try:
                    from ..oled_pages.ips import oled_page_ips
                    pages.append(oled_page_ips)
                except Exception as e:
                    self.log.error(f"Failed to import oled_page_ips: {e}")
            elif page_name == 'disk':
                try:
                    from ..oled_pages.disks import oled_page_disk
                    pages.append(oled_page_disk)
                except Exception as e:
                    self.log.error(f"Failed to import oled_page_disk: {e}")
            elif page_name == 'battery':
                try:
                    from ..oled_pages.battery import oled_page_battery
                    pages.append(oled_page_battery)
                except Exception as e:
                    self.log.error(f"Failed to import oled_page_battery: {e}")
            elif page_name == 'input':
                try:
                    from ..oled_pages.input import oled_page_input
                    pages.append(oled_page_input)
                except Exception as e:
                    self.log.error(f"Failed to import oled_page_input: {e}")
            elif page_name == 'output':
                try:
                    from ..oled_pages.output import oled_page_output
                    pages.append(oled_page_output)
                except Exception as e:
                    self.log.error(f"Failed to import oled_page_output: {e}")
            elif page_name == 'mix':
                try:
                    from ..oled_pages.mix import oled_page_mix
                    pages.append(oled_page_mix)
                except Exception as e:
                    self.log.error(f"Failed to import oled_page_mix: {e}")
                    
        # deduplicates
        # pages = list(set(pages))
        pages = list(dict.fromkeys(pages))

        return pages

    @log_error
    def loop(self):
        from ..oled_pages.power_off import oled_page_power_off

        pages = self.init_pages()
    
        pages_len = len(pages)
        page_index = 0
        last_page_index = -1
        last_refresh_time = 0

        if self.oled is None or not self.oled.is_ready():
            self.log.error("OLED service not ready")
            return

        self.wake_start_time = time.time()

        while self.running:
            if not self.enable:
                if self.wake_flag:
                    self.log.debug("OLED disabled, going to sleep")
                    self.sleep()
                continue
            
            if self.is_power_off == True:
                oled_page_power_off(self.oled)
                time.sleep(.5)
                continue

            if pages_len < 1:
                self.oled.draw_text(f'config error', 64, 20, align='center', size=16)
                self.oled.display()
                continue

            if self.button == 'single_click':
                if not self.wake_flag:
                    self.log.debug("OLED service waking up")
                    self.wake_flag = True
                    last_page_index = -1
                else:
                    page_index += 1
                    if page_index >= len(pages):
                        page_index = 0
                self.wake_start_time = time.time()
            elif self.button == 'double_click':
                if self.wake_flag:
                    page_index -= 1
                    if page_index < 0:
                        page_index = len(pages) - 1
                    self.wake_start_time = time.time()
                    
            if self.wake_flag:
                if last_page_index != page_index or time.time() - last_refresh_time > self.REFRESH_INTERVAL:
                    last_page_index = page_index
                    last_refresh_time = time.time()
                    pages[page_index](self.oled, self.config)

                if time.time() - self.wake_start_time > self.sleep_timeout:
                    self.log.debug("OLED sleep timeout, sleeping")
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

