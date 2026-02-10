from pm_auto.libs.ssd1306 import SSD1306

from pm_auto.libs.utils import log_error, constrain
from pm_auto.libs.addon import Addon

from .pages import power_off_page
from .pages import get_pages

import time
import asyncio

def get_available_pages(peripherals):
    available_pages = []
    for item in peripherals:
        if item.startswith("oled_page_"):
            available_pages.append(item.split("oled_page_")[1])
    return available_pages

class OLEDAddon(Addon):
    REFRESH_INTERVAL = 1 # seconds, how often to refresh the display
    MIN_SLEEP_TIMEOUT = 0 # 5s, minimum sleep timeout
    MAX_SLEEP_TIMEOUT = 3600 # 3600s, 10min, maximum sleep timeout

    DEFAULT_CONFIG = {
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

    @log_error
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.oled = SSD1306(rotation=self.rotation)
        except Exception as e:
            self.log.error(f"Failed to initialize OLED service: {e}")
            return
        self._is_ready = self.oled.is_ready()

        self.available_pages = get_available_pages(self.peripherals)

        self.wake_flag = True
        self.wake_start_time = 0
        self.is_power_off = False
        self.is_wake_page_next = False
        self.is_page_prev = False
        self.data = {}

        self.event.subscribe("oled_wake_page_next", self.wake_page_next)
        self.event.subscribe("oled_page_prev", self.page_prev)
        self.event.subscribe("shutdown", self.show_shutdown_screen)
        self.event.subscribe("oled_show_shutdown_screen", self.show_shutdown_screen)
        self.event.subscribe("data_changed", self.handle_data_changed)

    @log_error
    def handle_data_changed(self, data, delete_keys: list = []):
        # Delete old data
        for key in delete_keys:
            if key in self.data:
                del self.data[key]

        self.data.update(data)

    @log_error
    def update_config(self, config, init=False):
        '''
        Update config.

        Args:
            config (Dict): New config dict.

        Returns:
            A dict of config patch to update the config file.
        '''
        patch = {}
        if "oled_enable" in config:
            _enable = bool(config['oled_enable'])
            self.enable = _enable
            patch['oled_enable'] = _enable
            self.log.debug(f"Update oled_enable to {_enable}")
            if not init:
                if _enable:
                    self.wake()
                else:
                    self.sleep()
        if "oled_rotation" in config:
            _rotation = int(config['oled_rotation'])
            if _rotation not in [0, 90, 180, 270]:
                self.log.error("Invalid rotation value, must be 0, 90, 180, or 270")
            else:
                self.rotation = _rotation
                patch['oled_rotation'] = _rotation
                if not init:
                    self.set_rotation(_rotation)
                self.log.debug(f"Update oled_rotation to {_rotation}")
        if "scroll_interval" in config:
            _interval = int(config['scroll_interval'])
            self.scroll_interval = _interval
            patch['scroll_interval'] = _interval
            self.log.debug(f"Update scroll_interval to {_interval}")
        if "oled_sleep_timeout" in config:
            _timeout = int(config['oled_sleep_timeout'])

            if _timeout < self.MIN_SLEEP_TIMEOUT or _timeout > self.MAX_SLEEP_TIMEOUT:
                self.log.warning(f"Invalid sleep timeout value, must be between {self.MIN_SLEEP_TIMEOUT} and {self.MAX_SLEEP_TIMEOUT}")
                _timeout = constrain(_timeout, self.MIN_SLEEP_TIMEOUT, self.MAX_SLEEP_TIMEOUT)
            self.sleep_timeout = _timeout
            patch['oled_sleep_timeout'] = _timeout
            self.log.debug(f"Update oled_sleep_timeout to {_timeout}")
        if "temperature_unit" in config:
            _unit = config['temperature_unit']
            if _unit not in ['C', 'F']:
                self.log.error("Invalid temperature unit, must be 'C' or 'F'")
            else:
                self.temperature_unit = _unit
                patch['temperature_unit'] = _unit
                self.log.debug(f"Update temperature_unit to {_unit}")
        if "oled_pages" in config:
            new_pages = []
            for page in config['oled_pages']:
                if not init and page not in self.available_pages:
                    self.log.warning(f"Invalid oled page {page}, must be in {self.available_pages}")
                elif page in new_pages:
                    self.log.warning(f"Duplicate oled page {page}")
                else:
                    new_pages.append(page)
            if not init:
                self.update_pages(pages=new_pages)
            self.oled_pages = new_pages
            patch['oled_pages'] = new_pages
            self.log.debug(f"Update oled_pages to {self.oled_pages}")
        self.config.update(patch)
        return patch

    @log_error
    def set_rotation(self, rotation):
        self.oled.set_rotation(rotation)

    @log_error
    def show_shutdown_screen(self, reason):
        self.log.info(f"Show shutdown screen, reason: {reason}")
        self.is_power_off = True

    @log_error
    def wake(self):
        self.wake_start_time = time.time()
        self.wake_flag = True

    @log_error
    def wake_page_next(self, *args, **kwargs):
        self.log.debug(f'OLED wake or next page')
        self.is_wake_page_next = True

    @log_error
    def page_prev(self, *args, **kwargs):
        self.log.debug(f'OLED prev page')
        self.is_page_prev = True

    @log_error
    def sleep(self):
        self.log.debug(f'OLED sleep')
        self.wake_flag = False
        self.oled.clear()
        self.oled.display()

    @log_error
    def update_pages(self, pages=None):
        pages = pages or self.oled_pages
        self.pages = get_pages(pages)
        self.log.debug(f'Update pages to: {self.pages}')
        self.page_index = 0
        self.last_page_index = -1
        self.wake()

    @log_error
    async def _main(self):
        self.update_pages()
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
                await asyncio.sleep(1)
                continue
            
            if self.is_power_off == True:
                self.log.debug("OLED show power off page")
                power_off_page.main(self.oled)
                await asyncio.sleep(1)
                continue

            if len(self.pages) < 1:
                self.oled.draw_text(f'config error', 64, 20, align='center', size=16)
                self.oled.display()
                await asyncio.sleep(1)
                continue

            if self.is_wake_page_next:
                if not self.wake_flag:
                    self.log.debug("OLED service waking up")
                    self.wake_flag = True
                    self.last_page_index = -1
                else:
                    self.page_index += 1
                    if self.page_index >= len(self.pages):
                        self.page_index = 0
                self.wake_start_time = time.time()
                self.is_wake_page_next = False
            elif self.is_page_prev:
                if self.wake_flag:
                    self.page_index -= 1
                    if self.page_index < 0:
                        self.page_index = len(self.pages) - 1
                    self.wake_start_time = time.time()
                self.is_page_prev = False
                    
            if self.wake_flag:
                if self.last_page_index != self.page_index or time.time() - last_refresh_time > self.REFRESH_INTERVAL:
                    self.last_page_index = self.page_index
                    last_refresh_time = time.time()
                    page = self.pages[self.page_index]
                    page.main(self.oled, self.data, self.config)

                if self.sleep_timeout > 0 and time.time() - self.wake_start_time > self.sleep_timeout:
                    self.log.debug("OLED sleep timeout, sleeping")
                    self.sleep()
                    await asyncio.sleep(1)
                    continue

            await asyncio.sleep(.05)

    @log_error
    async def _stop(self):
        if self.oled is not None and self.oled.is_ready():
            self.oled.clear()
            self.oled.display()
            self.oled.off()

